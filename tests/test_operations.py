import math

import pytest

from app.exceptions import DivideByZeroError
from app.operations import AbsoluteDifference, IntegerDivide, OperationFactory, Percentage


@pytest.mark.parametrize(
	"name,expected",
	[
		("int_divide", IntegerDivide),
		("percent", Percentage),
		("abs_diff", AbsoluteDifference),
	],
)
def test_factory_supports_assignment_command_names(name, expected):
	operation = OperationFactory.create_operation(name)
	assert isinstance(operation, expected)


@pytest.mark.parametrize(
	"alias_name,canonical_name",
	[
		("integer_divide", "int_divide"),
		("percentage", "percent"),
		("absolute_difference", "abs_diff"),
	],
)
def test_factory_aliases_match_canonical_behavior(alias_name, canonical_name):
	alias_operation = OperationFactory.create_operation(alias_name)
	canonical_operation = OperationFactory.create_operation(canonical_name)
	assert alias_operation.execute(10, 4) == canonical_operation.execute(10, 4)


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
		("integer_divide", 10, 0, "Cannot perform integer division by zero"),
		("percentage", 10, 0, "Cannot calculate percentage with zero as denominator"),
	],
)
def test_operations_raise_divide_by_zero_error_for_division_cases(name, left, right, error_message):
	operation = OperationFactory.create_operation(name)
	with pytest.raises(DivideByZeroError, match=error_message):
		operation.execute(left, right)


@pytest.mark.parametrize(
	"name,left,right,error_message",
	[
		("root", 27, 0, "Cannot take the root with degree zero"),
		("modulus", 10, 0, "Cannot take modulus with zero"),
	],
)
def test_operations_raise_value_error_for_non_division_zero_cases(name, left, right, error_message):
	operation = OperationFactory.create_operation(name)
	with pytest.raises(ValueError, match=error_message):
		operation.execute(left, right)


@pytest.mark.parametrize("unknown_name", ["", "average", "unknown", "INT_DIVIDE"])
def test_factory_rejects_unknown_operations(unknown_name):
	with pytest.raises(ValueError, match="Unknown operation"):
		OperationFactory.create_operation(unknown_name)


def test_factory_available_operations_includes_required_command_names():
	available = set(OperationFactory.get_available_operations())
	assert {"int_divide", "percent", "abs_diff"}.issubset(available)


def test_factory_available_operations_match_expected_registry():
	assert set(OperationFactory.get_available_operations()) == {
		"add",
		"subtract",
		"multiply",
		"divide",
		"power",
		"root",
		"modulus",
		"int_divide",
		"percent",
		"abs_diff",
		"integer_divide",
		"percentage",
		"absolute",
		"absolute_difference",
	}


@pytest.mark.parametrize("operation_name", ["add", "int_divide", "percent", "abs_diff"])
def test_required_operations_expect_two_inputs(operation_name):
	operation = OperationFactory.create_operation(operation_name)
	with pytest.raises(TypeError):
		operation.execute(10)


@pytest.mark.parametrize("value,expected", [(-10, 10), (0, 0), (3.5, 3.5)])
def test_absolute_operation_cases(value, expected):
	operation = OperationFactory.create_operation("absolute")
	assert operation.execute(value) == expected
