import math

import pytest

from app.calculator import (
	Absolute,
	AbsoluteDifference,
	Add,
	BinaryOperation,
	Divide,
	IntegerDivide,
	Modulus,
	Multiply,
	Operation,
	OperationFactory,
	Percentage,
	Power,
	Root,
	Subtract,
	UnaryOperation,
)


def test_abstract_operation_execute_method_body_is_reachable():
	assert Operation.execute(None) is None


def test_binary_operation_executes_wrapped_callable():
	operation = BinaryOperation(lambda x, y: x + y)
	assert operation.execute(2, 3) == 5


def test_unary_operation_executes_wrapped_callable():
	operation = UnaryOperation(lambda x: x * 2)
	assert operation.execute(4) == 8


def test_add_operation():
	assert Add().execute(10, 5) == 15


def test_subtract_operation():
	assert Subtract().execute(10, 5) == 5


def test_multiply_operation():
	from app.calculator import Multiply

	assert Multiply().execute(10, 5) == 50


def test_divide_operation():
	assert Divide().execute(10, 5) == 2


def test_divide_by_zero_raises_value_error():
	with pytest.raises(ValueError, match="Cannot divide by zero"):
		Divide().execute(10, 0)


def test_power_operation():
	assert Power().execute(2, 3) == 8


def test_root_operation():
	assert Root().execute(27, 3) == 3


def test_root_with_zero_degree_raises_value_error():
	with pytest.raises(ValueError, match="Cannot take the root with degree zero"):
		Root().execute(27, 0)


def test_modulus_operation():
	assert Modulus().execute(10, 3) == 1


def test_modulus_with_zero_raises_value_error():
	with pytest.raises(ValueError, match="Cannot take modulus with zero"):
		Modulus().execute(10, 0)


def test_integer_divide_operation_returns_int():
	result = IntegerDivide().execute(10, 3)
	assert isinstance(result, int)
	assert result == 3


def test_integer_divide_by_zero_raises_value_error():
	with pytest.raises(ValueError, match="Cannot perform integer division by zero"):
		IntegerDivide().execute(10, 0)


def test_percentage_operation():
	assert Percentage().execute(25, 200) == 12.5


def test_percentage_with_zero_denominator_raises_value_error():
	with pytest.raises(ValueError, match="Cannot calculate percentage with zero as denominator"):
		Percentage().execute(10, 0)


def test_absolute_operation():
	assert Absolute().execute(-42) == 42


def test_absolute_difference_operation():
	assert AbsoluteDifference().execute(3, 10) == 7


def test_factory_create_operation_returns_expected_instances():
	expected_types = {
		"add": Add,
		"subtract": Subtract,
		"multiply": Multiply,
		"divide": Divide,
		"power": Power,
		"root": Root,
		"modulus": Modulus,
		"integer_divide": IntegerDivide,
		"percentage": Percentage,
		"absolute": Absolute,
		"absolute_difference": AbsoluteDifference,
	}

	for name, expected_type in expected_types.items():
		instance = OperationFactory.create_operation(name)
		assert isinstance(instance, expected_type)


def test_factory_get_available_operations_contains_all_registered_names():
	available = OperationFactory.get_available_operations()
	assert set(available) == {
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


def test_factory_create_unknown_operation_raises_value_error_with_available_operations():
	with pytest.raises(ValueError) as exc_info:
		OperationFactory.create_operation("unknown")

	message = str(exc_info.value)
	assert "Unknown operation: unknown" in message
	assert "Available operations" in message


def test_root_with_square_of_two_is_close():
	result = Root().execute(2, 2)
	assert math.isclose(result, math.sqrt(2))
