from datetime import datetime, timezone

import pandas as pd
import pytest

from app.calculation import Calculation
from app.calculator import Calculator
from app.exceptions import CalculatorError, PersistenceError
from app.history import HistoryManager


def test_persistence_error_inherits_calculator_error():
	assert issubclass(PersistenceError, CalculatorError)


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


def test_history_manager_add_get_clear_and_set_all():
	history = HistoryManager()
	first = Calculation("add", 1, 2, 3)
	second = Calculation("subtract", 4, 1, 3)

	history.add(first)
	history.set_all([first, second])
	assert history.get_all() == [first, second]

	history.clear()
	assert history.get_all() == []


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

	history = calculator.get_history()
	assert len(history) == 2
	assert history[0].operation == "add"
	assert history[1].result == 4


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
