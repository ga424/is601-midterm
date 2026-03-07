import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


# Environment variables used for configuration
ENV_LOG_DIR = "CALCULATOR_LOG_DIR"
ENV_HISTORY_DIR = "CALCULATOR_HISTORY_DIR"
ENV_LOG_FILE = "CALCULATOR_LOG_FILE"
ENV_HISTORY_FILE = "CALCULATOR_HISTORY_FILE"
ENV_MAX_HISTORY_SIZE = "CALCULATOR_MAX_HISTORY_SIZE"
ENV_AUTO_SAVE = "CALCULATOR_AUTO_SAVE"
ENV_PRECISION = "CALCULATOR_PRECISION"
ENV_MAX_INPUT_VALUE = "CALCULATOR_MAX_INPUT_VALUE"
ENV_DEFAULT_ENCODING = "CALCULATOR_DEFAULT_ENCODING"
ENV_REPL_PROMPT = "CALCULATOR_REPL_PROMPT"
ENV_REPL_WELCOME_MESSAGE = "CALCULATOR_REPL_WELCOME_MESSAGE"
ENV_REPL_USE_COLOR = "CALCULATOR_REPL_USE_COLOR"

# These utility functions are used to parse environment variable values into the appropriate data types (integers, floats, and booleans)
def parse_bool(raw_value: str, key: str) -> bool:
	normalized = raw_value.strip().lower()
	if normalized in {"true", "1", "yes", "on"}:
		return True
	if normalized in {"false", "0", "no", "off"}:
		return False
	raise ValueError(f"{key} must be a boolean value.")

def parse_int(raw_value: str, key: str) -> int:
	try:
		return int(raw_value)
	except ValueError as error:
		raise ValueError(f"{key} must be an integer.") from error

def parse_float(raw_value: str, key: str) -> float:
	try:
		return float(raw_value)
	except ValueError as error:
		raise ValueError(f"{key} must be a numeric value.") from error


# This module defines the CalculatorConfig data class, which is responsible for loading and validating the configuration settings for the calculator application from environment variables. 
@dataclass(frozen=True)
class CalculatorConfig:
	log_dir: Path
	history_dir: Path
	log_file_name: str
	history_file_name: str
	max_history_size: int
	auto_save: bool
	precision: int
	max_input_value: float
	default_encoding: str
	repl_prompt: str
	repl_welcome_message: str
	repl_use_color: bool

	# A property method that constructs the full path to the log file by combining the log directory and log file name.
	@property
	def log_file(self) -> Path:
		return self.log_dir / self.log_file_name

	# A property method that constructs the full path to the history file by combining the history directory and history file name.
	@property
	def history_file(self) -> Path:
		return self.history_dir / self.history_file_name

	# This is a class method that loads the configuration settings from environment variables, validates them, and returns an instance of CalculatorConfig with the loaded settings.
	# It also ensures that the necessary directories for logs and history exist.
	@classmethod
	def load(cls, env_file: str | None = None) -> "CalculatorConfig":
	
		if env_file is None:
			load_dotenv(override=False)
		else:
			load_dotenv(dotenv_path=env_file, override=False)

		log_dir = Path(os.getenv(ENV_LOG_DIR, "logs"))
		history_dir = Path(os.getenv(ENV_HISTORY_DIR, "history"))
		log_file_name = os.getenv(ENV_LOG_FILE, "calculator.log").strip()
		history_file_name = os.getenv(ENV_HISTORY_FILE, "history.csv").strip()

		max_history_size = parse_int(os.getenv(ENV_MAX_HISTORY_SIZE, "100"), ENV_MAX_HISTORY_SIZE)
		auto_save = parse_bool(os.getenv(ENV_AUTO_SAVE, "true"), ENV_AUTO_SAVE)
		precision = parse_int(os.getenv(ENV_PRECISION, "10"), ENV_PRECISION)
		max_input_value = parse_float(os.getenv(ENV_MAX_INPUT_VALUE, "1000000"), ENV_MAX_INPUT_VALUE)
		default_encoding = os.getenv(ENV_DEFAULT_ENCODING, "utf-8").strip()
		repl_prompt = os.getenv(ENV_REPL_PROMPT, "calc> ")
		repl_welcome_message = os.getenv(
			ENV_REPL_WELCOME_MESSAGE,
			"Calculator REPL started. Type 'help' for available commands.",
		)
		repl_use_color = parse_bool(os.getenv(ENV_REPL_USE_COLOR, "true"), ENV_REPL_USE_COLOR)

		if max_history_size <= 0:
			raise ValueError(f"{ENV_MAX_HISTORY_SIZE} must be greater than zero.")
		if precision < 0:
			raise ValueError(f"{ENV_PRECISION} must be zero or greater.")
		if max_input_value <= 0:
			raise ValueError(f"{ENV_MAX_INPUT_VALUE} must be greater than zero.")
		if not default_encoding:
			raise ValueError(f"{ENV_DEFAULT_ENCODING} cannot be empty.")
		if not log_file_name:
			raise ValueError(f"{ENV_LOG_FILE} cannot be empty.")
		if not history_file_name:
			raise ValueError(f"{ENV_HISTORY_FILE} cannot be empty.")
		if not repl_prompt:
			raise ValueError(f"{ENV_REPL_PROMPT} cannot be empty.")
		if not repl_welcome_message:
			raise ValueError(f"{ENV_REPL_WELCOME_MESSAGE} cannot be empty.")

		log_dir.mkdir(parents=True, exist_ok=True)
		history_dir.mkdir(parents=True, exist_ok=True)

		return cls(
			log_dir=log_dir,
			history_dir=history_dir,
			log_file_name=log_file_name,
			history_file_name=history_file_name,
			max_history_size=max_history_size,
			auto_save=auto_save,
			precision=precision,
			max_input_value=max_input_value,
			default_encoding=default_encoding,
			repl_prompt=repl_prompt,
			repl_welcome_message=repl_welcome_message,
			repl_use_color=repl_use_color,
		)
