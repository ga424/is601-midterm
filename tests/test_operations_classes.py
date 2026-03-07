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
from app.operations import (
	Absolute as OpsAbsolute,
	AbsoluteDifference as OpsAbsoluteDifference,
	Add as OpsAdd,
	BinaryOperation as OpsBinaryOperation,
	Divide as OpsDivide,
	IntegerDivide as OpsIntegerDivide,
	Modulus as OpsModulus,
	Multiply as OpsMultiply,
	Operation as OpsOperation,
	OperationFactory as OpsOperationFactory,
	Percentage as OpsPercentage,
	Power as OpsPower,
	Root as OpsRoot,
	Subtract as OpsSubtract,
	UnaryOperation as OpsUnaryOperation,
)


def test_abstract_operation_execute_method_body_is_reachable():
	assert Operation.execute(None) is None


def test_binary_operation_executes_wrapped_callable():
	operation = BinaryOperation(lambda x, y: x + y)
	assert operation.execute(2, 3) == 5


def test_unary_operation_executes_wrapped_callable():
	operation = UnaryOperation(lambda x: x * 2)
	assert operation.execute(4) == 8


def test_calculator_reexports_operation_symbols_from_operations_module():
	assert Add is OpsAdd
	assert Subtract is OpsSubtract
	assert Multiply is OpsMultiply
	assert Divide is OpsDivide
	assert Power is OpsPower
	assert Root is OpsRoot
	assert Modulus is OpsModulus
	assert IntegerDivide is OpsIntegerDivide
	assert Percentage is OpsPercentage
	assert Absolute is OpsAbsolute
	assert AbsoluteDifference is OpsAbsoluteDifference
	assert Operation is OpsOperation
	assert BinaryOperation is OpsBinaryOperation
	assert UnaryOperation is OpsUnaryOperation
	assert OperationFactory is OpsOperationFactory
