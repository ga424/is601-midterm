from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pytest

from app.calculation import Calculation
from app.calculator import Calculator, colorize_output, run_repl
from app.calculator_config import (
	ENV_AUTO_SAVE,
	ENV_DEFAULT_ENCODING,
	ENV_HISTORY_DIR,
	ENV_LOG_DIR,
	ENV_MAX_HISTORY_SIZE,
	ENV_MAX_INPUT_VALUE,
	ENV_PRECISION,
	CalculatorConfig,
	parse_bool,
	parse_float,
	parse_int,
)
from app.calculator_memento import CalculatorCaretaker
from app.exceptions import CalculatorError, PersistenceError
from app.history import HistoryManager
from app.input_validators import parse_number, validate_max_input, validate_operation_name
from app.logger import AutoSaveObserver, Logger, LoggingObserver


def _clear_config_env(monkeypatch):
	for key in [
		ENV_LOG_DIR,
		ENV_HISTORY_DIR,
		ENV_MAX_HISTORY_SIZE,
		ENV_AUTO_SAVE,
		ENV_PRECISION,
		ENV_MAX_INPUT_VALUE,
		ENV_DEFAULT_ENCODING,
	]:
		monkeypatch.delenv(key, raising=False)


@pytest.mark.parametrize(
	"value,expected",
	[("true", True), ("1", True), ("yes", True), ("on", True), ("false", False), ("0", False), ("no", False), ("off", False)],
)
def test_parse_bool_variants(value, expected):
	assert parse_bool(value, ENV_AUTO_SAVE) is expected


def test_parse_bool_invalid_raises_value_error():
	with pytest.raises(ValueError, match=f"{ENV_AUTO_SAVE} must be a boolean value"):
		parse_bool("maybe", ENV_AUTO_SAVE)


def test_parse_int_returns_integer_value():
	assert parse_int("42", ENV_MAX_HISTORY_SIZE) == 42


def test_parse_int_invalid_raises_value_error():
	with pytest.raises(ValueError, match=f"{ENV_MAX_HISTORY_SIZE} must be an integer"):
		parse_int("4.2", ENV_MAX_HISTORY_SIZE)


def test_parse_float_returns_float_value():
	assert parse_float("42.5", ENV_MAX_INPUT_VALUE) == 42.5


def test_parse_float_invalid_raises_value_error():
	with pytest.raises(ValueError, match=f"{ENV_MAX_INPUT_VALUE} must be a numeric value"):
		parse_float("abc", ENV_MAX_INPUT_VALUE)


def test_load_uses_defaults_and_creates_directories(monkeypatch, tmp_path):
	_clear_config_env(monkeypatch)
	monkeypatch.chdir(tmp_path)

	config = CalculatorConfig.load(env_file=str(tmp_path / "missing.env"))

	assert config.max_history_size == 100
	assert config.auto_save is True
	assert config.precision == 10
	assert config.max_input_value == 1_000_000.0
	assert config.default_encoding == "utf-8"
	assert config.log_dir.name == "logs"
	assert config.history_dir.name == "history"
	assert config.log_dir.exists()
	assert config.history_dir.exists()
	assert config.log_file.name == "calculator.log"
	assert config.history_file.name == "history.csv"


def test_load_uses_env_values(monkeypatch, tmp_path):
	_clear_config_env(monkeypatch)
	monkeypatch.setenv(ENV_LOG_DIR, str(tmp_path / "my-logs"))
	monkeypatch.setenv(ENV_HISTORY_DIR, str(tmp_path / "my-history"))
	monkeypatch.setenv(ENV_MAX_HISTORY_SIZE, "250")
	monkeypatch.setenv(ENV_AUTO_SAVE, "false")
	monkeypatch.setenv(ENV_PRECISION, "6")
	monkeypatch.setenv(ENV_MAX_INPUT_VALUE, "9999.5")
	monkeypatch.setenv(ENV_DEFAULT_ENCODING, "latin-1")

	config = CalculatorConfig.load(env_file=str(tmp_path / "missing.env"))

	assert config.max_history_size == 250
	assert config.auto_save is False
	assert config.precision == 6
	assert config.max_input_value == 9999.5
	assert config.default_encoding == "latin-1"
	assert config.log_dir == tmp_path / "my-logs"
	assert config.history_dir == tmp_path / "my-history"


def test_load_rejects_invalid_bounds(monkeypatch, tmp_path):
	_clear_config_env(monkeypatch)
	monkeypatch.setenv(ENV_MAX_HISTORY_SIZE, "0")
	with pytest.raises(ValueError, match=f"{ENV_MAX_HISTORY_SIZE} must be greater than zero"):
		CalculatorConfig.load(env_file=str(tmp_path / "missing.env"))

	_clear_config_env(monkeypatch)
	monkeypatch.setenv(ENV_PRECISION, "-1")
	with pytest.raises(ValueError, match=f"{ENV_PRECISION} must be zero or greater"):
		CalculatorConfig.load(env_file=str(tmp_path / "missing.env"))

	_clear_config_env(monkeypatch)
	monkeypatch.setenv(ENV_MAX_INPUT_VALUE, "0")
	with pytest.raises(ValueError, match=f"{ENV_MAX_INPUT_VALUE} must be greater than zero"):
		CalculatorConfig.load(env_file=str(tmp_path / "missing.env"))


def test_load_works_when_env_file_is_none(monkeypatch, tmp_path):
	_clear_config_env(monkeypatch)
	monkeypatch.chdir(tmp_path)
	config = CalculatorConfig.load()
	assert config.log_dir.exists()
	assert config.history_dir.exists()


def test_load_rejects_empty_encoding(monkeypatch, tmp_path):
	_clear_config_env(monkeypatch)
	monkeypatch.setenv(ENV_DEFAULT_ENCODING, "   ")
	with pytest.raises(ValueError, match=f"{ENV_DEFAULT_ENCODING} cannot be empty"):
		CalculatorConfig.load(env_file=str(tmp_path / "missing.env"))


class DummyObserver:
	def __init__(self):
		self.calls = []

	def update(self, calculation: Calculation) -> None:
		self.calls.append(calculation)


def test_calculation_to_dict_and_from_dict_round_trip():
	original = Calculation(
		operation="multiply",
		operand_1=4,
		operand_2=5,
		result=20,
		timestamp=datetime(2026, 3, 6, tzinfo=timezone.utc),
	)
	payload = original.to_dict()
	restored = Calculation.from_dict(payload)
	assert restored == original


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


def test_logger_and_logging_observer_write_to_file(tmp_path):
	log_file = tmp_path / "events.log"
	logger = Logger(log_file=log_file)
	logger.info("hello")
	observer = LoggingObserver(logger)
	observer.update(Calculation("add", 1, 2, 3))
	content = log_file.read_text(encoding="utf-8")
	assert "INFO:hello" in content
	assert "operation=add" in content


def test_autosave_observer_saves_when_enabled(tmp_path):
	history = HistoryManager()
	history.add(Calculation("add", 1, 2, 3))
	csv_file = tmp_path / "history" / "calc.csv"
	observer = AutoSaveObserver(history=history, csv_file=csv_file, enabled=True)
	observer.update(Calculation("add", 0, 0, 0))
	frame = pd.read_csv(csv_file)
	assert list(frame["operation"]) == ["add"]


def test_autosave_observer_disabled_does_not_write_file(tmp_path):
	history = HistoryManager()
	history.add(Calculation("add", 1, 2, 3))
	csv_file = tmp_path / "history" / "calc.csv"
	observer = AutoSaveObserver(history=history, csv_file=csv_file, enabled=False)
	observer.update(Calculation("add", 0, 0, 0))
	assert not csv_file.exists()


def test_calculator_calculate_history_observers_and_unregister(tmp_path):
	calculator = Calculator(history_file=tmp_path / "history.csv")
	dummy = DummyObserver()
	calculator.register_observer(dummy)
	result = calculator.calculate("add", 10, 2)
	assert result.result == 12
	assert len(calculator.get_history()) == 1
	assert dummy.calls[-1] == result
	calculator.unregister_observer(dummy)
	calculator.calculate("subtract", 10, 5)
	assert len(dummy.calls) == 1


def test_calculator_invalid_input_raises_calculator_error(tmp_path):
	calculator = Calculator(history_file=tmp_path / "history.csv")
	with pytest.raises(CalculatorError):
		calculator.calculate("add", "x", 2)


def test_calculator_wrapped_generic_exception_raises_calculator_error(tmp_path, monkeypatch):
	calculator = Calculator(history_file=tmp_path / "history.csv")

	def broken_factory(_name):
		raise RuntimeError("boom")

	from app import operations

	monkeypatch.setattr(operations.OperationFactory, "create_operation", broken_factory)
	with pytest.raises(CalculatorError, match="boom"):
		calculator.calculate("add", 1, 2)


def test_calculator_undo_redo_and_clear(tmp_path):
	calculator = Calculator(history_file=tmp_path / "history.csv")
	assert calculator.undo() is None
	calculator.calculate("add", 1, 2)
	calculator.calculate("multiply", 2, 5)
	assert len(calculator.get_history()) == 2
	assert calculator.undo() is not None
	assert len(calculator.get_history()) == 1
	assert calculator.redo() is not None
	assert len(calculator.get_history()) == 2
	calculator.clear_history()
	assert calculator.get_history() == []


def test_save_and_load_history(tmp_path):
	file_path = tmp_path / "saved.csv"
	calculator = Calculator(history_file=file_path)
	calculator.calculate("add", 1, 2)
	calculator.save_history()
	assert file_path.exists()
	calculator.clear_history()
	calculator.load_history()
	assert len(calculator.get_history()) == 1


def test_save_history_error_wraps_persistence_error(tmp_path, monkeypatch):
	calculator = Calculator(history_file=tmp_path / "history.csv")
	calculator.calculate("add", 1, 2)

	def broken_to_csv(*args, **kwargs):
		raise OSError("disk full")

	monkeypatch.setattr(pd.DataFrame, "to_csv", broken_to_csv)
	with pytest.raises(PersistenceError, match="Failed to save history"):
		calculator.save_history(tmp_path / "x.csv")


def test_load_history_error_cases(tmp_path, monkeypatch):
	calculator = Calculator(history_file=tmp_path / "missing.csv")
	with pytest.raises(PersistenceError, match="History file not found"):
		calculator.load_history()

	bad_columns = tmp_path / "bad_columns.csv"
	pd.DataFrame([{"operation": "add", "result": 2}]).to_csv(bad_columns, index=False)
	with pytest.raises(PersistenceError, match="missing required columns"):
		calculator.load_history(bad_columns)

	bad_rows = tmp_path / "bad_rows.csv"
	pd.DataFrame([
		{
			"operation": "add",
			"operand_1": "x",
			"operand_2": 2,
			"result": 3,
			"timestamp": "invalid-date",
		}
	]).to_csv(bad_rows, index=False)
	with pytest.raises(PersistenceError, match="invalid row data"):
		calculator.load_history(bad_rows)

	def broken_read_csv(*args, **kwargs):
		raise pd.errors.ParserError("bad csv")

	monkeypatch.setattr(pd, "read_csv", broken_read_csv)
	with pytest.raises(PersistenceError, match="Failed to read history file"):
		calculator.load_history(bad_rows)


def test_run_command_flow_and_messages(tmp_path):
	calculator = Calculator(history_file=tmp_path / "history.csv")

	message, should_exit = calculator.run_command("   ")
	assert message == "Please enter a command."
	assert should_exit is False

	help_message, _ = calculator.run_command("help")
	assert "Available commands" in help_message

	redo_message, _ = calculator.run_command("redo")
	assert redo_message == "Nothing to redo."

	op_message, _ = calculator.run_command("int_divide 10 3")
	assert op_message == "integer_divide(10.0, 3.0) = 3"

	history_message, _ = calculator.run_command("history")
	assert "integer_divide(10.0, 3.0) = 3" in history_message

	undo_message, _ = calculator.run_command("undo")
	assert undo_message == "Undo successful."

	redo_message2, _ = calculator.run_command("redo")
	assert redo_message2 == "Redo successful."

	save_message, _ = calculator.run_command("save")
	assert save_message == "History saved."

	load_message, _ = calculator.run_command("load")
	assert load_message == "History loaded."

	clear_message, _ = calculator.run_command("clear")
	assert clear_message == "History cleared."

	exit_message, should_exit = calculator.run_command("exit")
	assert exit_message == "Exiting calculator."
	assert should_exit is True


def test_run_command_usage_and_error_messages(tmp_path):
	calculator = Calculator(history_file=tmp_path / "history.csv")
	message, _ = calculator.run_command("add 10")
	assert message == "Operations require exactly two numeric operands."

	message, _ = calculator.run_command("save a b")
	assert message == "Error: save accepts zero or one file path argument."

	message, _ = calculator.run_command("load a b")
	assert message == "Error: load accepts zero or one file path argument."

	message, _ = calculator.run_command("add one two")
	assert message.startswith("Error:")


def test_run_command_history_empty_and_path_based_save_load(tmp_path):
	calculator = Calculator(history_file=tmp_path / "default.csv")
	message, _ = calculator.run_command("history")
	assert message == "History is empty."

	calculator.run_command("add 1 2")
	file_path = tmp_path / "named.csv"
	message, _ = calculator.run_command(f"save {file_path}")
	assert message == "History saved."
	calculator.run_command("clear")
	message, _ = calculator.run_command(f"load {file_path}")
	assert message == "History loaded."


def test_run_command_returns_error_on_persistence_failure(tmp_path):
	calculator = Calculator(history_file=tmp_path / "missing.csv")
	message, _ = calculator.run_command("load")
	assert message.startswith("Error: History file not found")


def test_run_command_save_returns_error_on_persistence_failure(tmp_path, monkeypatch):
	calculator = Calculator(history_file=tmp_path / "history.csv")

	def broken_save(_path=None):
		raise PersistenceError("save failed")

	monkeypatch.setattr(calculator, "save_history", broken_save)
	message, _ = calculator.run_command("save bad.csv")
	assert message == "Error: save failed"


def test_run_repl_exits_when_exit_command_received(monkeypatch, capsys):
	calculator = Calculator(history_file=Path("history.csv"))
	inputs = iter(["help", "exit"])
	monkeypatch.setattr("builtins.input", lambda _prompt: next(inputs))

	run_repl(calculator)

	output = capsys.readouterr().out
	assert "Available commands" in output
	assert "Exiting calculator." in output


def test_run_repl_handles_keyboard_interrupt(monkeypatch, capsys):
	def raise_keyboard_interrupt(_prompt):
		raise KeyboardInterrupt

	monkeypatch.setattr("builtins.input", raise_keyboard_interrupt)
	run_repl(Calculator())
	assert "Exiting calculator." in capsys.readouterr().out


def test_run_repl_handles_unexpected_exception(monkeypatch, capsys):
	inputs = iter(["help", "exit"])

	def flaky_input(_prompt):
		value = next(inputs)
		if value == "help":
			raise RuntimeError("input broke")
		return value

	monkeypatch.setattr("builtins.input", flaky_input)
	run_repl(Calculator())
	assert "Error: input broke" in capsys.readouterr().out


def test_module_run_command_function_returns_exit_sentinel(tmp_path):
	from app.calculator import run_command

	calculator = Calculator(history_file=tmp_path / "history.csv")
	assert run_command(calculator, "help").startswith("Available commands")
	assert run_command(calculator, "exit") == "exit"


def test_colorize_output_variants():
	assert colorize_output("done", level="success", use_color=False) == "done"
	assert "ok" in colorize_output("ok", level="success", use_color=True)
	assert "failed" in colorize_output("failed", level="error", use_color=True)
	assert "watch out" in colorize_output("watch out", level="warning", use_color=True)
	assert "hello" in colorize_output("hello", level="other", use_color=True)
	assert "custom" in colorize_output("custom", color="red", use_color=True)


def test_colorize_output_with_mocked_colorama_palette_paths(monkeypatch):
	class _Fore:
		GREEN = "G"
		RED = "R"
		YELLOW = "Y"
		CYAN = "C"

	class _Style:
		RESET_ALL = "!"

	class _Colorama:
		Fore = _Fore
		Style = _Style

	import sys

	monkeypatch.setitem(sys.modules, "colorama", _Colorama)
	assert colorize_output("ok", level="success") == "Gok!"
	assert colorize_output("ok", color="green") == "Gok!"
	assert colorize_output("ok", color="unknown") == "Cok!"


def test_validator_helpers_cover_error_branches():
	with pytest.raises(Exception):
		parse_number(True)

	with pytest.raises(Exception):
		validate_max_input(99, 10)

	assert validate_max_input(9, 10) == 9

	with pytest.raises(Exception):
		validate_operation_name("", ["add"])

	with pytest.raises(Exception):
		validate_operation_name("unknown", ["add"])
