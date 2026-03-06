import pytest

from app.exceptions import CalculatorError, OperationError, PersistenceError, ValidationError
from app.input_validators import (
	parse_number,
	validate_max_input,
	validate_operation_name,
	validate_two_numbers,
)


def test_custom_exceptions_inherit_from_base_calculator_error():
	assert issubclass(OperationError, CalculatorError)
	assert issubclass(ValidationError, CalculatorError)
	assert issubclass(PersistenceError, CalculatorError)


@pytest.mark.parametrize(
	"value,expected",
	[
		(10, 10.0),
		("12.5", 12.5),
		(-4.2, -4.2),
	],
)
def test_parse_number_accepts_valid_numeric_values(value, expected):
	assert parse_number(value) == expected


def test_parse_number_rejects_bool_value():
	with pytest.raises(ValidationError, match="must be a number, got bool"):
		parse_number(True, field_name="operand")


@pytest.mark.parametrize("value", [None, "abc", object()])
def test_parse_number_rejects_non_numeric_values(value):
	with pytest.raises(ValidationError, match="must be numeric"):
		parse_number(value, field_name="operand")


def test_validate_max_input_passes_when_no_limit_is_set():
	assert validate_max_input(101.2, None) == 101.2


def test_validate_max_input_accepts_values_inside_limit():
	assert validate_max_input(-10.0, 10.0, field_name="left") == -10.0


def test_validate_max_input_rejects_value_outside_limit():
	with pytest.raises(ValidationError, match="exceeds maximum allowed value"):
		validate_max_input(10.1, 10.0, field_name="left")


def test_validate_two_numbers_parses_and_returns_both_values():
	left, right = validate_two_numbers("3.5", 2)
	assert left == 3.5
	assert right == 2.0


def test_validate_two_numbers_applies_max_limit_to_both_values():
	with pytest.raises(ValidationError, match="right exceeds maximum allowed value"):
		validate_two_numbers(5, 11, max_input_value=10, right_name="right")


def test_validate_operation_name_normalizes_valid_name():
	result = validate_operation_name("  ADD  ", ["add", "subtract"])
	assert result == "add"


@pytest.mark.parametrize("name", [None, "", "   "])
def test_validate_operation_name_rejects_blank_or_non_string(name):
	with pytest.raises(ValidationError, match="non-empty string"):
		validate_operation_name(name, ["add"])  # type: ignore[arg-type]


def test_validate_operation_name_rejects_unknown_operation_with_available_list():
	with pytest.raises(ValidationError, match="Available operations: add, subtract"):
		validate_operation_name("multiply", ["add", "subtract"])
