from datetime import datetime, timezone

from app.calculation import Calculation
from app.calculator import Calculator
from app.calculator_memento import CalculatorCaretaker
from app.history import HistoryManager


def test_calculation_timestamp_defaults_to_datetime():
	calculation = Calculation("add", 1, 2, 3)
	assert isinstance(calculation.timestamp, datetime)


def test_calculation_to_dict_and_from_dict_round_trip():
	original = Calculation(
		operation="multiply",
		operand_1=3,
		operand_2=4,
		result=12,
		timestamp=datetime(2026, 3, 1, tzinfo=timezone.utc),
	)
	payload = original.to_dict()
	restored = Calculation.from_dict(payload)

	assert restored == original


def test_history_manager_rejects_non_positive_size():
	try:
		HistoryManager(max_size=0)
		assert False
	except ValueError as error:
		assert "greater than zero" in str(error)


def test_history_manager_add_and_last_with_trimming():
	history = HistoryManager(max_size=2)
	history.add(Calculation("add", 1, 1, 2))
	history.add(Calculation("add", 2, 2, 4))
	history.add(Calculation("add", 3, 3, 6))

	items = history.get_all()
	assert len(items) == 2
	assert items[0].result == 4
	assert history.last().result == 6


def test_history_manager_clear_and_last_when_empty():
	history = HistoryManager(max_size=3)
	history.add(Calculation("subtract", 10, 3, 7))
	history.clear()

	assert history.get_all() == []
	assert history.last() is None


def test_history_manager_set_all_respects_max_size():
	history = HistoryManager(max_size=2)
	history.set_all(
		[
			Calculation("add", 1, 2, 3),
			Calculation("add", 2, 3, 5),
			Calculation("add", 3, 4, 7),
		]
	)

	items = history.get_all()
	assert [item.result for item in items] == [5, 7]


def test_caretaker_undo_and_redo_round_trip():
	caretaker = CalculatorCaretaker()
	state_1 = [Calculation("add", 1, 1, 2)]
	state_2 = [Calculation("add", 1, 1, 2), Calculation("add", 2, 2, 4)]

	caretaker.save_for_undo(state_1)
	undone = caretaker.undo(state_2)
	assert undone == state_1

	redone = caretaker.redo(undone)
	assert redone == state_2


def test_caretaker_undo_and_redo_return_none_without_state():
	caretaker = CalculatorCaretaker()
	assert caretaker.undo([]) is None
	assert caretaker.redo([]) is None


def test_calculator_calculate_adds_history_entry():
	calculator = Calculator(max_history_size=3)
	calc = calculator.calculate("add", 10, 5)

	assert calc.result == 15
	assert len(calculator.history.get_all()) == 1


def test_calculator_undo_and_redo_flow():
	calculator = Calculator(max_history_size=5)
	calculator.calculate("add", 1, 1)
	calculator.calculate("multiply", 2, 3)

	assert len(calculator.history.get_all()) == 2
	assert calculator.undo() is True
	assert len(calculator.history.get_all()) == 1

	assert calculator.redo() is True
	assert len(calculator.history.get_all()) == 2


def test_calculator_undo_and_redo_without_state_return_false():
	calculator = Calculator(max_history_size=2)
	assert calculator.undo() is False
	assert calculator.redo() is False


def test_calculator_clear_history_can_be_undone():
	calculator = Calculator(max_history_size=2)
	calculator.calculate("add", 5, 5)
	calculator.clear_history()

	assert calculator.history.get_all() == []
	assert calculator.undo() is True
	assert len(calculator.history.get_all()) == 1
