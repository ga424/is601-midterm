import pandas as pd
import pytest

from app.calculation import Calculation
from app.calculator import Calculator
from app.exceptions import CalculatorError, PersistenceError
from app.history import HistoryManager
from app.input_validators import parse_number, validate_max_input, validate_operation_name
from app.logger import AutoSaveObserver, Logger, LoggingObserver


class DummyObserver:
	def __init__(self):
		self.calls = []

	def update(self, calculation: Calculation) -> None:
		self.calls.append(calculation)


def test_logger_and_logging_observer_write_to_file(tmp_path):
	log_file = tmp_path / "events.log"
	logger = Logger(log_file=log_file)
	logger.info("hello")
	observer = LoggingObserver(logger)
	observer.update(Calculation("add", 1, 2, 3))
	content = log_file.read_text(encoding="utf-8")
	assert "time=" in content
	assert "level=INFO" in content
	assert "class=Logger" in content
	assert "message=hello" in content
	assert "operation=add" in content
	assert "class=LoggingObserver" in content


def test_calculator_event_logging_writes_command_and_history_events(tmp_path):
	log_file = tmp_path / "events.log"
	history_file = tmp_path / "history.csv"
	calculator = Calculator(history_file=history_file, log_file=log_file)

	calculator.run_command("help")
	calculator.run_command("add 2 3")
	calculator.run_command("save")
	calculator.run_command("load")
	calculator.run_command("clear")
	calculator.run_command("undo")
	calculator.run_command("redo")
	calculator.run_command("exit")

	content = log_file.read_text(encoding="utf-8")
	assert "event=calculator_initialized" in content
	assert "event=command_received command=help" in content
	assert "event=calculation_requested operation=add" in content
	assert "event=calculation_completed operation=add result=5.0" in content
	assert "class=Calculator" in content
	assert "event=history_saved" in content
	assert "event=history_loaded" in content
	assert "event=history_cleared" in content
	assert "event=command_response action=exit" in content


def test_calculator_event_logging_writes_error_events(tmp_path):
	log_file = tmp_path / "events.log"
	calculator = Calculator(history_file=tmp_path / "missing.csv", log_file=log_file)
	calculator.run_command("load")

	content = log_file.read_text(encoding="utf-8")
	assert "event=history_load_missing_file" in content
	assert "event=command_response action=load" in content


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


def test_calculator_respects_precision_setting(tmp_path):
	calculator = Calculator(history_file=tmp_path / "history.csv", precision=2)
	result = calculator.calculate("divide", 1, 3)
	assert result.result == 0.33


def test_calculator_respects_max_input_value(tmp_path):
	calculator = Calculator(history_file=tmp_path / "history.csv", max_input_value=10)
	with pytest.raises(CalculatorError, match="exceeds maximum allowed value"):
		calculator.calculate("add", 11, 1)


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
