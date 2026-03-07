import math

import pytest

from app.calculator import OperationFactory


@pytest.mark.parametrize(
	"name,left,right,expected",
	[
		("add", 10, 5, 15),
		("subtract", 10, 5, 5),
		("multiply", 10, 5, 50),
		("divide", 10, 5, 2),
		("power", 2, 3, 8),
		("modulus", 10, 3, 1),
		("integer_divide", 10, 3, 3),
		("percentage", 25, 200, 12.5),
		("absolute_difference", 3, 10, 7),
	],
)
def test_factory_operations_execute_expected_results(name, left, right, expected):
	operation = OperationFactory.create_operation(name)
	assert operation.execute(left, right) == expected


@pytest.mark.parametrize("left,right", [(27, 3), (16, 4), (81, 2)])
def test_root_operation_expected_values(left, right):
	operation = OperationFactory.create_operation("root")
	result = operation.execute(left, right)
	expected = left ** (1 / right)
	assert math.isclose(result, expected)


@pytest.mark.parametrize(
	"name,left,right,error_message",
	[
		("divide", 10, 0, "Cannot divide by zero"),
		("root", 27, 0, "Cannot take the root with degree zero"),
		("modulus", 10, 0, "Cannot take modulus with zero"),
		("integer_divide", 10, 0, "Cannot perform integer division by zero"),
		("percentage", 10, 0, "Cannot calculate percentage with zero as denominator"),
	],
)
def test_operations_raise_value_error_for_zero_division_cases(name, left, right, error_message):
	operation = OperationFactory.create_operation(name)
	with pytest.raises(ValueError, match=error_message):
		operation.execute(left, right)


@pytest.mark.parametrize("unknown_name", ["", "average", "unknown", "INT_DIVIDE"])
def test_factory_rejects_unknown_operations(unknown_name):
	with pytest.raises(ValueError, match="Unknown operation"):
		OperationFactory.create_operation(unknown_name)


def test_factory_available_operations_match_expected_registry():
	assert set(OperationFactory.get_available_operations()) == {
		"add",
		"subtract",
		"multiply",
		"divide",
		"power",
		"root",
		"modulus",
		"integer_divide",
		"percentage",
		"absolute",
		"absolute_difference",
	}


@pytest.mark.parametrize("value,expected", [(-10, 10), (0, 0), (3.5, 3.5)])
def test_absolute_operation_cases(value, expected):
	operation = OperationFactory.create_operation("absolute")
	assert operation.execute(value) == expected
