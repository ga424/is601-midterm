import pytest

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


def test_factory_available_operations_includes_required_command_names():
	available = set(OperationFactory.get_available_operations())
	assert {"int_divide", "percent", "abs_diff"}.issubset(available)


@pytest.mark.parametrize("operation_name", ["add", "int_divide", "percent", "abs_diff"])
def test_required_operations_expect_two_inputs(operation_name):
	operation = OperationFactory.create_operation(operation_name)

	with pytest.raises(TypeError):
		operation.execute(10)
