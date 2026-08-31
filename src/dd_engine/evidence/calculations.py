"""Safe deterministic recomputation for versioned calculation records."""

from __future__ import annotations

import ast
from decimal import ROUND_HALF_EVEN, ROUND_HALF_UP, Decimal, InvalidOperation

from dd_engine.evidence.models import JsonObject

_ROUNDING = {"half_even": ROUND_HALF_EVEN, "half_up": ROUND_HALF_UP}


class CalculationExpressionError(ValueError):
    """Raised when a stored formula is not in the small deterministic expression language."""


def _decimal(value: object) -> Decimal:
    if isinstance(value, bool) or value is None:
        raise CalculationExpressionError("normalized input is not numeric")
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise CalculationExpressionError(f"normalized input is not numeric: {value!r}") from exc


def _evaluate(node: ast.AST, values: dict[str, Decimal]) -> Decimal:
    if isinstance(node, ast.Expression):
        return _evaluate(node.body, values)
    if isinstance(node, ast.Name):
        if node.id not in values:
            raise CalculationExpressionError(f"formula references unknown input {node.id}")
        return values[node.id]
    if (
        isinstance(node, ast.Constant)
        and isinstance(node.value, int | float)
        and not isinstance(node.value, bool)
    ):
        return Decimal(str(node.value))
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.UAdd | ast.USub):
        value = _evaluate(node.operand, values)
        return value if isinstance(node.op, ast.UAdd) else -value
    if isinstance(node, ast.BinOp):
        left = _evaluate(node.left, values)
        right = _evaluate(node.right, values)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            if right == 0:
                raise CalculationExpressionError("formula divides by zero")
            return left / right
    raise CalculationExpressionError(
        "formula contains unsupported syntax; only input names, numeric constants "
        "and + - * / are allowed"
    )


def _formula_names(expression: str) -> set[str]:
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise CalculationExpressionError(f"formula is not valid expression syntax: {exc}") from exc
    names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    _evaluate(tree, {name: Decimal(1) for name in names})
    return names


def _rounded(value: Decimal, rounding: JsonObject) -> Decimal:
    places = int(rounding["decimal_places"])
    mode = str(rounding["mode"])
    if mode == "none":
        return value
    quantum = Decimal(1).scaleb(-places)
    return value.quantize(quantum, rounding=_ROUNDING[mode])


def recompute_calculation(record: JsonObject) -> JsonObject:
    """Independently evaluate one deterministic calculation without mutating its record."""

    calculation_id = str(record.get("calculation_id", "unknown"))
    method = record.get("calculation_method")
    if method == "model_assisted":
        return {
            "calculation_id": calculation_id,
            "errors": [],
            "formula_input_ids": [],
            "observed_recomputed_value": None,
            "status": "not_applicable_model_assisted",
        }

    raw_inputs = record.get("source_inputs")
    inputs = raw_inputs if isinstance(raw_inputs, list | tuple) else []
    missing_ids = [
        str(item.get("input_id"))
        for item in inputs
        if isinstance(item, dict) and item.get("missing") is True
    ]
    if missing_ids:
        result = record.get("result")
        errors = []
        if isinstance(result, dict) and result.get("recomputed_value") is not None:
            errors.append("missing inputs must leave result.recomputed_value null")
        if record.get("independent_recomputation_status") != "blocked_missing_inputs":
            errors.append(
                "missing inputs require independent_recomputation_status=blocked_missing_inputs"
            )
        return {
            "calculation_id": calculation_id,
            "errors": errors,
            "formula_input_ids": [],
            "missing_input_ids": missing_ids,
            "observed_recomputed_value": None,
            "status": "blocked_missing_inputs",
        }

    try:
        formula = record["formula"]
        expression = str(formula["expression"])
        formula_names = _formula_names(expression)
        values: dict[str, Decimal] = {}
        for item in inputs:
            if not isinstance(item, dict):
                raise CalculationExpressionError("source input is not an object")
            input_id = str(item["input_id"])
            if not input_id.isidentifier():
                raise CalculationExpressionError(
                    f"input ID {input_id!r} is not a valid formula identifier"
                )
            values[input_id] = _decimal(item.get("normalized_value"))
        if formula_names != set(values):
            missing_from_formula = sorted(set(values) - formula_names)
            unknown_in_formula = sorted(formula_names - set(values))
            details = []
            if missing_from_formula:
                details.append(f"unused inputs: {', '.join(missing_from_formula)}")
            if unknown_in_formula:
                details.append(f"unknown inputs: {', '.join(unknown_in_formula)}")
            raise CalculationExpressionError("formula/input mismatch (" + "; ".join(details) + ")")
        tree = ast.parse(expression, mode="eval")
        observed = _rounded(_evaluate(tree, values), record["rounding"])
        result = record["result"]
        stored = result.get("recomputed_value")
        errors = []
        if stored is None:
            errors.append("deterministic calculation has no stored recomputed_value")
        elif _decimal(stored) != observed:
            errors.append(
                f"stored recomputed_value {stored!r} does not equal independent result "
                f"{str(observed)!r}"
            )
        expected_status = "verified" if not errors else "failed"
        recorded_status = record.get("independent_recomputation_status")
        if recorded_status not in {expected_status, "variance_identified"}:
            errors.append(
                f"independent_recomputation_status {recorded_status!r} is inconsistent "
                "with recomputation"
            )
        return {
            "calculation_id": calculation_id,
            "errors": errors,
            "formula_input_ids": sorted(formula_names),
            "observed_recomputed_value": str(observed),
            "status": "verified" if not errors else "failed",
        }
    except (CalculationExpressionError, KeyError, TypeError, ValueError) as exc:
        return {
            "calculation_id": calculation_id,
            "errors": [str(exc)],
            "formula_input_ids": [],
            "observed_recomputed_value": None,
            "status": "failed",
        }
