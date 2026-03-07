import pytest

from app.calculation import Calculation
from app.calculator_memento import CalculatorCaretaker
from app.history import HistoryManager


def test_history_manager_add_set_clear_and_last():
	history = HistoryManager(max_size=2)
	first = Calculation("add", 1, 2, 3)
	second = Calculation("multiply", 2, 3, 6)
	third = Calculation("subtract", 9, 1, 8)
	history.add(first)
	history.add(second)
	history.add(third)
	assert history.get_all() == [second, third]
	assert history.last() == third
	history.clear()
	assert history.get_all() == []


def test_history_manager_rejects_non_positive_max_size():
	with pytest.raises(ValueError, match="max_size must be greater than zero"):
		HistoryManager(max_size=0)


def test_caretaker_undo_redo_round_trip():
	calc_1 = Calculation("add", 1, 2, 3)
	calc_2 = Calculation("multiply", 2, 3, 6)
	caretaker = CalculatorCaretaker()
	caretaker.save_for_undo([])
	caretaker.save_for_undo([calc_1])
	assert caretaker.undo([calc_1, calc_2]) == [calc_1]
	assert caretaker.redo([calc_1]) == [calc_1, calc_2]


def test_caretaker_undo_redo_empty_stacks_return_none():
	caretaker = CalculatorCaretaker()
	assert caretaker.undo([]) is None
	assert caretaker.redo([]) is None
