from pathlib import Path

import pandas as pd

from app.calculation import Calculation
from app.calculator import Calculator
from app.history import HistoryManager
from app.logger import AutoSaveObserver, Logger, LoggingObserver


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


def test_history_manager_add_get_and_clear():
	history = HistoryManager()
	history.add(Calculation("add", 2, 3, 5))

	assert len(history.get_all()) == 1
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


def test_calculator_calculate_stores_history_and_returns_calculation():
	calculator = Calculator()
	calculation = calculator.calculate("divide", 10, 2)

	assert calculation.result == 5
	assert calculator.history.get_all() == [calculation]
