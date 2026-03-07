from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pytest

from app.calculation import Calculation
from app.calculator import Calculator, run_repl
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
from app.exceptions import CalculatorError, PersistenceError
from app.history import HistoryManager
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


def test_load_works_when_env_file_is_none(monkeypatch, tmp_path):
	_clear_config_env(monkeypatch)
	monkeypatch.chdir(tmp_path)

	config = CalculatorConfig.load()

	assert config.log_dir.name == "logs"
	assert config.history_dir.name == "history"
	assert config.log_dir.exists()
	assert config.history_dir.exists()


def test_load_rejects_non_positive_max_history(monkeypatch, tmp_path):
	_clear_config_env(monkeypatch)
	monkeypatch.setenv(ENV_MAX_HISTORY_SIZE, "0")

	with pytest.raises(ValueError, match=f"{ENV_MAX_HISTORY_SIZE} must be greater than zero"):
		CalculatorConfig.load(env_file=str(tmp_path / "missing.env"))


def test_load_rejects_negative_precision(monkeypatch, tmp_path):
	_clear_config_env(monkeypatch)
	monkeypatch.setenv(ENV_PRECISION, "-1")

	with pytest.raises(ValueError, match=f"{ENV_PRECISION} must be zero or greater"):
		CalculatorConfig.load(env_file=str(tmp_path / "missing.env"))


def test_load_rejects_non_positive_max_input(monkeypatch, tmp_path):
	_clear_config_env(monkeypatch)
	monkeypatch.setenv(ENV_MAX_INPUT_VALUE, "0")

	with pytest.raises(ValueError, match=f"{ENV_MAX_INPUT_VALUE} must be greater than zero"):
		CalculatorConfig.load(env_file=str(tmp_path / "missing.env"))


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


def test_calculation_to_dict_contains_expected_fields():
	calculation = Calculation("add", 1, 2, 3)
	payload = calculation.to_dict()

	assert payload["operation"] == "add"
	assert payload["operand_1"] == 1
	assert payload["operand_2"] == 2
	assert payload["result"] == 3
	assert isinstance(payload["timestamp"], str)


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


def test_history_manager_add_clear_set_all_get_all():
	history = HistoryManager()
	first = Calculation("add", 1, 2, 3)
	second = Calculation("multiply", 2, 3, 6)
	history.add(first)
	history.set_all([first, second])
	assert history.get_all() == [first, second]
	history.clear()
	assert history.get_all() == []


def test_calculator_notifies_registered_observer():
	calculator = Calculator()
	observer = DummyObserver()
	calculator.register_observer(observer)

	calculation = calculator.calculate("add", 10, 5)
	assert observer.calls == [calculation]


def test_calculator_unregister_observer_stops_notifications():
	calculator = Calculator()
	observer = DummyObserver()
	calculator.register_observer(observer)
	calculator.unregister_observer(observer)
	calculator.calculate("multiply", 2, 4)
	assert observer.calls == []


def test_calculator_unregister_missing_observer_noop():
	calculator = Calculator()
	calculator.unregister_observer(DummyObserver())
	assert calculator.history.get_all() == []


def test_logger_writes_info_message_to_file(tmp_path):
	log_file = tmp_path / "calculator.log"
	logger = Logger(log_file=log_file)
	logger.info("test message")
	content = log_file.read_text(encoding="utf-8")
	assert "INFO:test message" in content


def test_logging_observer_logs_calculation(tmp_path):
	log_file = tmp_path / "events.log"
	observer = LoggingObserver(Logger(log_file=log_file))
	calculation = Calculation("subtract", 8, 3, 5)
	observer.update(calculation)
	content = log_file.read_text(encoding="utf-8")
	assert "operation=subtract" in content
	assert "result=5" in content


def test_autosave_observer_saves_history_to_csv(tmp_path):
	history = HistoryManager()
	history.add(Calculation("add", 1, 2, 3))
	history.add(Calculation("multiply", 2, 5, 10))
	csv_file = tmp_path / "history" / "calc_history.csv"
	observer = AutoSaveObserver(history=history, csv_file=csv_file, enabled=True)
	observer.update(Calculation("add", 0, 0, 0))
	assert csv_file.exists()
	frame = pd.read_csv(csv_file)
	assert list(frame["operation"]) == ["add", "multiply"]
	assert list(frame["result"]) == [3, 10]


def test_autosave_observer_disabled_does_not_write_file(tmp_path):
	history = HistoryManager()
	history.add(Calculation("add", 1, 2, 3))
	csv_file = Path(tmp_path / "history.csv")
	observer = AutoSaveObserver(history=history, csv_file=csv_file, enabled=False)
	observer.update(Calculation("add", 0, 0, 0))
	assert not csv_file.exists()


def test_persistence_error_inherits_calculator_error():
	assert issubclass(PersistenceError, CalculatorError)


def test_calculator_calculate_get_history_and_clear_history():
	calculator = Calculator()
	result = calculator.calculate("add", 10, 2)
	assert result.result == 12
	assert len(calculator.get_history()) == 1
	calculator.clear_history()
	assert calculator.get_history() == []


def test_save_history_creates_csv_with_expected_columns(tmp_path):
	calculator = Calculator()
	calculator.calculate("add", 1, 2)
	calculator.calculate("multiply", 3, 4)
	file_path = tmp_path / "history" / "calc.csv"
	calculator.save_history(str(file_path))
	assert file_path.exists()
	frame = pd.read_csv(file_path)
	assert list(frame.columns) == ["operation", "operand_1", "operand_2", "result", "timestamp"]
	assert list(frame["operation"]) == ["add", "multiply"]


def test_save_history_with_empty_history_writes_header_only(tmp_path):
	calculator = Calculator()
	file_path = tmp_path / "empty.csv"
	calculator.save_history(str(file_path))
	frame = pd.read_csv(file_path)
	assert frame.empty
	assert list(frame.columns) == ["operation", "operand_1", "operand_2", "result", "timestamp"]


def test_load_history_populates_history_from_csv(tmp_path):
	file_path = tmp_path / "loaded.csv"
	rows = [
		{
			"operation": "add",
			"operand_1": 3,
			"operand_2": 7,
			"result": 10,
			"timestamp": "2026-03-06T00:00:00+00:00",
		},
		{
			"operation": "divide",
			"operand_1": 8,
			"operand_2": 2,
			"result": 4,
			"timestamp": "2026-03-06T00:00:01+00:00",
		},
	]
	pd.DataFrame(rows).to_csv(file_path, index=False)

	calculator = Calculator()
	calculator.load_history(str(file_path))
	assert len(calculator.get_history()) == 2
	assert calculator.get_history()[0].operation == "add"
	assert calculator.get_history()[1].result == 4


def test_load_history_missing_file_raises_persistence_error(tmp_path):
	calculator = Calculator()
	missing_path = tmp_path / "missing.csv"
	with pytest.raises(PersistenceError, match="History file not found"):
		calculator.load_history(str(missing_path))


def test_load_history_missing_required_columns_raises_persistence_error(tmp_path):
	file_path = tmp_path / "bad_columns.csv"
	pd.DataFrame([{"operation": "add", "result": 2}]).to_csv(file_path, index=False)
	calculator = Calculator()
	with pytest.raises(PersistenceError, match="missing required columns"):
		calculator.load_history(str(file_path))


def test_load_history_invalid_row_data_raises_persistence_error(tmp_path):
	file_path = tmp_path / "bad_data.csv"
	pd.DataFrame(
		[
			{
				"operation": "add",
				"operand_1": "x",
				"operand_2": 2,
				"result": 3,
				"timestamp": "invalid-date",
			}
		]
	).to_csv(file_path, index=False)
	calculator = Calculator()
	with pytest.raises(PersistenceError, match="invalid row data"):
		calculator.load_history(str(file_path))


def test_save_history_io_failure_raises_persistence_error(tmp_path, monkeypatch):
	calculator = Calculator()
	calculator.calculate("add", 1, 2)

	def broken_to_csv(*args, **kwargs):
		raise OSError("disk full")

	monkeypatch.setattr(pd.DataFrame, "to_csv", broken_to_csv)
	with pytest.raises(PersistenceError, match="Failed to save history"):
		calculator.save_history(str(tmp_path / "history.csv"))


def test_load_history_parser_failure_raises_persistence_error(tmp_path, monkeypatch):
	file_path = tmp_path / "history.csv"
	file_path.write_text("operation,operand_1\nadd,1", encoding="utf-8")

	def broken_read_csv(*args, **kwargs):
		raise pd.errors.ParserError("bad csv")

	monkeypatch.setattr(pd, "read_csv", broken_read_csv)
	calculator = Calculator()
	with pytest.raises(PersistenceError, match="Failed to read history file"):
		calculator.load_history(str(file_path))


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
	assert message == "integer_divide(10.0, 3.0) = 3"
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
	redo_message, _ = calculator.run_command("redo")
	assert redo_message == "Nothing to redo."

	calculator.run_command("add 1 2")
	undo_message, _ = calculator.run_command("undo")
	assert undo_message == "Undo successful."

	redo_message, _ = calculator.run_command("redo")
	assert redo_message == "Redo successful."


def test_run_command_unknown_system_usage_message():
	calculator = Calculator()
	message, _ = calculator.run_command("save extra another")
	assert message == "Error: save accepts zero or one file path argument."


def test_run_command_load_usage_error_message():
	calculator = Calculator()
	message, _ = calculator.run_command("load a b")
	assert message == "Error: load accepts zero or one file path argument."


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
	assert message == "Error: History file is malformed: missing required columns."


def test_run_repl_exits_when_exit_command_received(monkeypatch, capsys):
	calculator = Calculator()
	inputs = iter(["help", "exit"])
	monkeypatch.setattr("builtins.input", lambda _prompt: next(inputs))

	run_repl(calculator)

	output = capsys.readouterr().out
	assert "Available commands" in output
	assert "Exiting calculator." in output
