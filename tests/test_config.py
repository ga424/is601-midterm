import pytest

from app.calculator_config import (
	ENV_AUTO_SAVE,
	ENV_DEFAULT_ENCODING,
	ENV_HISTORY_DIR,
	ENV_HISTORY_FILE,
	ENV_LOG_FILE,
	ENV_LOG_LEVEL,
	ENV_LOG_DIR,
	ENV_MAX_HISTORY_SIZE,
	ENV_MAX_INPUT_VALUE,
	ENV_PRECISION,
	ENV_REPL_PROMPT,
	ENV_REPL_USE_COLOR,
	ENV_REPL_WELCOME_MESSAGE,
	CalculatorConfig,
	parse_bool,
	parse_float,
	parse_int,
)


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


def test_load_uses_defaults_and_creates_directories(clear_config_env, monkeypatch, tmp_path):
	monkeypatch.chdir(tmp_path)

	config = CalculatorConfig.load(env_file=str(tmp_path / "missing.env"))

	assert config.max_history_size == 100
	assert config.auto_save is True
	assert config.precision == 10
	assert config.max_input_value == 1_000_000.0
	assert config.default_encoding == "utf-8"
	assert config.log_level == "INFO"
	assert config.log_dir.name == "logs"
	assert config.history_dir.name == "history"
	assert config.log_dir.exists()
	assert config.history_dir.exists()
	assert config.log_file.name == "calculator.log"
	assert config.history_file.name == "history.csv"
	assert config.repl_prompt == "calc> "
	assert config.repl_welcome_message == "Calculator REPL started. Type 'help' for available commands."
	assert config.repl_use_color is True


def test_load_uses_env_values(clear_config_env, monkeypatch, tmp_path):
	monkeypatch.setenv(ENV_LOG_DIR, str(tmp_path / "my-logs"))
	monkeypatch.setenv(ENV_HISTORY_DIR, str(tmp_path / "my-history"))
	monkeypatch.setenv(ENV_LOG_FILE, "my-calculator.log")
	monkeypatch.setenv(ENV_LOG_LEVEL, "debug")
	monkeypatch.setenv(ENV_HISTORY_FILE, "my-history.csv")
	monkeypatch.setenv(ENV_MAX_HISTORY_SIZE, "250")
	monkeypatch.setenv(ENV_AUTO_SAVE, "false")
	monkeypatch.setenv(ENV_PRECISION, "6")
	monkeypatch.setenv(ENV_MAX_INPUT_VALUE, "9999.5")
	monkeypatch.setenv(ENV_DEFAULT_ENCODING, "latin-1")
	monkeypatch.setenv(ENV_REPL_PROMPT, "mycalc> ")
	monkeypatch.setenv(ENV_REPL_WELCOME_MESSAGE, "Welcome to calculator")
	monkeypatch.setenv(ENV_REPL_USE_COLOR, "false")

	config = CalculatorConfig.load(env_file=str(tmp_path / "missing.env"))

	assert config.max_history_size == 250
	assert config.auto_save is False
	assert config.precision == 6
	assert config.max_input_value == 9999.5
	assert config.default_encoding == "latin-1"
	assert config.log_level == "DEBUG"
	assert config.log_dir == tmp_path / "my-logs"
	assert config.history_dir == tmp_path / "my-history"
	assert config.log_file.name == "my-calculator.log"
	assert config.history_file.name == "my-history.csv"
	assert config.repl_prompt == "mycalc> "
	assert config.repl_welcome_message == "Welcome to calculator"
	assert config.repl_use_color is False


def test_load_rejects_invalid_bounds(clear_config_env, monkeypatch, tmp_path):
	monkeypatch.setenv(ENV_MAX_HISTORY_SIZE, "0")
	with pytest.raises(ValueError, match=f"{ENV_MAX_HISTORY_SIZE} must be greater than zero"):
		CalculatorConfig.load(env_file=str(tmp_path / "missing.env"))

	monkeypatch.delenv(ENV_MAX_HISTORY_SIZE, raising=False)
	monkeypatch.setenv(ENV_PRECISION, "-1")
	with pytest.raises(ValueError, match=f"{ENV_PRECISION} must be zero or greater"):
		CalculatorConfig.load(env_file=str(tmp_path / "missing.env"))

	monkeypatch.delenv(ENV_PRECISION, raising=False)
	monkeypatch.setenv(ENV_MAX_INPUT_VALUE, "0")
	with pytest.raises(ValueError, match=f"{ENV_MAX_INPUT_VALUE} must be greater than zero"):
		CalculatorConfig.load(env_file=str(tmp_path / "missing.env"))


def test_load_works_when_env_file_is_none(clear_config_env, monkeypatch, tmp_path):
	monkeypatch.chdir(tmp_path)
	config = CalculatorConfig.load()
	assert config.log_dir.exists()
	assert config.history_dir.exists()


def test_load_rejects_empty_encoding(clear_config_env, monkeypatch, tmp_path):
	monkeypatch.setenv(ENV_DEFAULT_ENCODING, "   ")
	with pytest.raises(ValueError, match=f"{ENV_DEFAULT_ENCODING} cannot be empty"):
		CalculatorConfig.load(env_file=str(tmp_path / "missing.env"))


def test_load_rejects_empty_file_names(clear_config_env, monkeypatch, tmp_path):
	monkeypatch.setenv(ENV_LOG_FILE, "   ")
	with pytest.raises(ValueError, match=f"{ENV_LOG_FILE} cannot be empty"):
		CalculatorConfig.load(env_file=str(tmp_path / "missing.env"))

	monkeypatch.delenv(ENV_LOG_FILE, raising=False)
	monkeypatch.setenv(ENV_HISTORY_FILE, "")
	with pytest.raises(ValueError, match=f"{ENV_HISTORY_FILE} cannot be empty"):
		CalculatorConfig.load(env_file=str(tmp_path / "missing.env"))


def test_load_rejects_invalid_log_level(clear_config_env, monkeypatch, tmp_path):
	monkeypatch.setenv(ENV_LOG_LEVEL, "verbose")
	with pytest.raises(ValueError, match=f"{ENV_LOG_LEVEL} must be one of"):
		CalculatorConfig.load(env_file=str(tmp_path / "missing.env"))


def test_load_rejects_empty_repl_text_values(clear_config_env, monkeypatch, tmp_path):
	monkeypatch.setenv(ENV_REPL_PROMPT, "")
	with pytest.raises(ValueError, match=f"{ENV_REPL_PROMPT} cannot be empty"):
		CalculatorConfig.load(env_file=str(tmp_path / "missing.env"))

	monkeypatch.delenv(ENV_REPL_PROMPT, raising=False)
	monkeypatch.setenv(ENV_REPL_WELCOME_MESSAGE, "")
	with pytest.raises(ValueError, match=f"{ENV_REPL_WELCOME_MESSAGE} cannot be empty"):
		CalculatorConfig.load(env_file=str(tmp_path / "missing.env"))
