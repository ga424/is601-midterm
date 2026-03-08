import pandas as pd

from app.calculation import Calculation
from app.calculator import Calculator
from app.history import HistoryManager
from app.logger import AutoSaveObserver, Logger, LoggingObserver


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


def test_logger_warning_and_error_write_levels(tmp_path):
	log_file = tmp_path / "events.log"
	logger = Logger(log_file=log_file)
	logger.warning("watch out")
	logger.error("failed")
	content = log_file.read_text(encoding="utf-8")
	assert "level=WARNING" in content
	assert "message=watch out" in content
	assert "level=ERROR" in content
	assert "message=failed" in content


def test_logger_event_respects_explicit_level(tmp_path):
	log_file = tmp_path / "events.log"
	logger = Logger(log_file=log_file)
	logger.event("threshold_warning", class_name="Logger", level="warning")
	logger.event("threshold_error", class_name="Logger", level="error")
	content = log_file.read_text(encoding="utf-8")
	assert "level=WARNING" in content
	assert "event=threshold_warning" in content
	assert "level=ERROR" in content
	assert "event=threshold_error" in content


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
