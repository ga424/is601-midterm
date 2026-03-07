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
