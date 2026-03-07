from pathlib import Path

import pandas as pd

from app.calculation import Calculation
from app.calculator import Calculator, run_repl
from app.history import HistoryManager


def test_calculation_to_dict_and_from_dict_round_trip():
	calculation = Calculation("add", 2, 3, 5)
	loaded = Calculation.from_dict(calculation.to_dict())
	assert loaded == calculation


def test_history_manager_add_clear_set_all_get_all():
	history = HistoryManager()
	first = Calculation("add", 1, 2, 3)
	second = Calculation("multiply", 2, 3, 6)
	history.add(first)
	history.set_all([first, second])
	assert history.get_all() == [first, second]
	history.clear()
	assert history.get_all() == []


def test_run_command_requires_input():
	calculator = Calculator()
	message, should_exit = calculator.run_command("   ")
	assert message == "Please enter a command."
	assert should_exit is False


def test_run_command_help_and_exit():
	calculator = Calculator()
	help_message, should_exit = calculator.run_command("help")
	assert "Available commands" in help_message
	assert should_exit is False

	exit_message, should_exit = calculator.run_command("exit")
	assert exit_message == "Exiting calculator."
	assert should_exit is True


def test_run_command_operation_success_with_alias_name():
	calculator = Calculator()
	message, should_exit = calculator.run_command("int_divide 10 3")
	assert "integer_divide(10.0, 3.0) = 3" == message
	assert should_exit is False


def test_run_command_operation_requires_two_operands():
	calculator = Calculator()
	message, _ = calculator.run_command("add 10")
	assert message == "Operations require exactly two numeric operands."


def test_run_command_operation_numeric_error():
	calculator = Calculator()
	message, _ = calculator.run_command("add one two")
	assert message.startswith("Error:")


def test_run_command_history_and_clear_flow():
	calculator = Calculator()
	empty_message, _ = calculator.run_command("history")
	assert empty_message == "History is empty."

	calculator.run_command("add 1 2")
	history_message, _ = calculator.run_command("history")
	assert "add(1.0, 2.0) = 3.0" in history_message

	clear_message, _ = calculator.run_command("clear")
	assert clear_message == "History cleared."


def test_run_command_undo_redo_flow():
	calculator = Calculator()
	message, _ = calculator.run_command("undo")
	assert message == "Nothing to undo."

	calculator.run_command("add 1 2")
	undo_message, _ = calculator.run_command("undo")
	assert undo_message == "Undo successful."

	redo_message, _ = calculator.run_command("redo")
	assert redo_message == "Redo successful."


def test_run_command_unknown_system_usage_message():
	calculator = Calculator()
	message, _ = calculator.run_command("save extra another")
	assert message.startswith("Error:")


def test_save_and_load_history_commands(tmp_path):
	file_path = tmp_path / "history.csv"
	calculator = Calculator(history_file=str(file_path))

	calculator.run_command("add 2 3")
	save_message, _ = calculator.run_command("save")
	assert save_message == "History saved."
	assert file_path.exists()

	calculator.run_command("clear")
	load_message, _ = calculator.run_command("load")
	assert load_message == "History loaded."
	assert len(calculator.history.get_all()) == 1


def test_load_command_missing_file_returns_error(tmp_path):
	calculator = Calculator(history_file=str(tmp_path / "missing.csv"))
	message, _ = calculator.run_command("load")
	assert message.startswith("Error: History file not found")


def test_load_command_malformed_csv_returns_error(tmp_path):
	bad_file = Path(tmp_path / "bad.csv")
	pd.DataFrame([{"operation": "add"}]).to_csv(bad_file, index=False)
	calculator = Calculator(history_file=str(bad_file))

	message, _ = calculator.run_command("load")
	assert message == "Error: History file is malformed."


def test_run_repl_exits_when_exit_command_received(monkeypatch, capsys):
	calculator = Calculator()
	inputs = iter(["help", "exit"])
	monkeypatch.setattr("builtins.input", lambda _prompt: next(inputs))

	run_repl(calculator)

	output = capsys.readouterr().out
	assert "Available commands" in output
	assert "Exiting calculator." in output
