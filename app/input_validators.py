from collections.abc import Iterable

from app.exceptions import ValidationError


def parse_number(value, field_name: str = "value") -> float:
	if isinstance(value, bool):
		raise ValidationError(f"{field_name} must be a number, got bool.")

	try:
		return float(value)
	except (TypeError, ValueError) as error:
		raise ValidationError(f"{field_name} must be numeric, got {value!r}.") from error


def validate_max_input(value: float, max_input_value: float | None, field_name: str = "value") -> float:
	if max_input_value is None:
		return value

	if abs(value) > max_input_value:
		raise ValidationError(
			f"{field_name} exceeds maximum allowed value of {max_input_value}."
		)

	return value


def validate_two_numbers(
	left,
	right,
	max_input_value: float | None = None,
	left_name: str = "left",
	right_name: str = "right",
) -> tuple[float, float]:
	parsed_left = parse_number(left, left_name)
	parsed_right = parse_number(right, right_name)

	valid_left = validate_max_input(parsed_left, max_input_value, left_name)
	valid_right = validate_max_input(parsed_right, max_input_value, right_name)

	return valid_left, valid_right


def validate_operation_name(operation_name: str, allowed_operations: Iterable[str]) -> str:
	if not isinstance(operation_name, str) or not operation_name.strip():
		raise ValidationError("operation name must be a non-empty string.")

	normalized = operation_name.strip().lower()
	allowed = {name.lower() for name in allowed_operations}
	if normalized not in allowed:
		available = ", ".join(sorted(allowed))
		raise ValidationError(
			f"Unknown operation '{normalized}'. Available operations: {available}"
		)

	return normalized
