import pytest

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
