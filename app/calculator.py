from pathlib import Path
from dataclasses import dataclass, field

import pandas as pd

from app.calculation import Calculation
from app.calculator_memento import CalculatorCaretaker
from app.exceptions import CalculatorError, PersistenceError
from app.history import HistoryManager
from app.input_validators import ValidationError, validate_operation_name, validate_two_numbers
from app.logger import AutoSaveObserver, Logger, LoggingObserver
from app.operations import (
	Absolute,
	AbsoluteDifference,
	Add,
	BinaryOperation,
	Divide,
	IntegerDivide,
	Modulus,
	Multiply,
	Operation,
	OperationFactory,
	Percentage,
	Power,
	Root,
	Subtract,
	UnaryOperation,
)


class Calculator:
	_OPERATION_COMMANDS = {
		"add",
		"subtract",
		"multiply",
		"divide",
		"power",
		"root",
		"modulus",
		"int_divide",
		"percent",
		"abs_diff",
		"integer_divide",
		"percentage",
		"absolute_difference",
		"absolute",
	}

	def __init__(
		self,
		history_file: str | Path = "history.csv",
		max_history_size: int = 100,
		log_file: str | Path = "calculator.log",
		auto_save: bool = True,
		precision: int = 10,
		max_input_value: float | None = None,
		default_encoding: str = "utf-8",
	):
		self.history = HistoryManager(max_size=max_history_size)
		self.history_file = Path(history_file)
		self.log_file = Path(log_file)
		self.precision = precision
		self.max_input_value = max_input_value
		self.default_encoding = default_encoding
		self._caretaker = CalculatorCaretaker()
		self._observers = []
		self._command_handlers = {
			"help": self._handle_help,
			"?": self._handle_help,
			"exit": self._handle_exit,
			"quit": self._handle_exit,
			"history": self._handle_history,
			"clear": self._handle_clear,
			"undo": self._handle_undo,
			"redo": self._handle_redo,
			"save": self._handle_save,
			"load": self._handle_load,
		}
		self._event_logger = Logger(log_file=self.log_file)
		self.register_observer(LoggingObserver(Logger(log_file=self.log_file)))
		self.register_observer(AutoSaveObserver(history=self.history, csv_file=self.history_file, enabled=auto_save))
		self._log_event(
			"calculator_initialized",
			history_file=self.history_file,
			log_file=self.log_file,
			max_history_size=max_history_size,
			auto_save=auto_save,
			precision=precision,
			max_input_value=max_input_value,
			default_encoding=default_encoding,
		)

	def _log_event(self, event: str, **details) -> None:
		self._event_logger.event(event, class_name=self.__class__.__name__, **details)

	def register_observer(self, observer) -> None:
		self._observers.append(observer)
		self._log_event("observer_registered", observer=observer.__class__.__name__)

	def unregister_observer(self, observer) -> None:
		if observer in self._observers:
			self._observers.remove(observer)
			self._log_event("observer_unregistered", observer=observer.__class__.__name__)

	def notify_observers(self, calculation: Calculation) -> None:
		for observer in self._observers:
			observer.update(calculation)

	def calculate(self, operation_name, left, right) -> Calculation:
		try:
			self._log_event("calculation_requested", operation=operation_name, left=left, right=right)
			normalized = validate_operation_name(operation_name, OperationFactory.get_available_operations())
			validated_left, validated_right = validate_two_numbers(
				left,
				right,
				max_input_value=self.max_input_value,
			)
			operation = OperationFactory.create_operation(normalized)
			raw_result = operation.execute(validated_left, validated_right)
			result = round(raw_result, self.precision)
			calculation = Calculation(normalized, validated_left, validated_right, result)
			self._caretaker.save_for_undo(self.history.get_all())
			self._caretaker.clear_redo()
			self.history.add(calculation)
			self.notify_observers(calculation)
			self._log_event("calculation_completed", operation=normalized, result=result)
			return calculation
		except ValidationError as error:
			self._log_event("calculation_validation_error", error=error)
			raise CalculatorError(str(error)) from error
		except Exception as error:
			self._log_event("calculation_error", error=error)
			raise CalculatorError(str(error)) from error

	def get_history(self) -> list[Calculation]:
		return self.history.get_all()

	def clear_history(self) -> None:
		self._caretaker.save_for_undo(self.history.get_all())
		self._caretaker.clear_redo()
		self.history.clear()
		self._log_event("history_cleared")

	def undo(self) -> Calculation | None:
		previous_state = self._caretaker.undo(self.history.get_all())
		if previous_state is None:
			self._log_event("undo_noop")
			return None
		self.history.set_all(previous_state)
		self._log_event("undo_applied", history_size=len(self.history.get_all()))
		return self.history.last()

	def redo(self) -> Calculation | None:
		next_state = self._caretaker.redo(self.history.get_all())
		if next_state is None:
			self._log_event("redo_noop")
			return None
		self.history.set_all(next_state)
		self._log_event("redo_applied", history_size=len(self.history.get_all()))
		return self.history.last()

	def save_history(self, file_path: str | Path | None = None) -> None:
		target = Path(file_path) if file_path else self.history_file
		rows = [calculation.to_dict() for calculation in self.history.get_all()]
		frame = pd.DataFrame(rows, columns=["operation", "operand_1", "operand_2", "result", "timestamp"])
		try:
			target.parent.mkdir(parents=True, exist_ok=True)
			frame.to_csv(target, index=False, encoding=self.default_encoding)
			self._log_event("history_saved", target=target, rows=len(rows))
		except Exception as error:
			self._log_event("history_save_error", target=target, error=error)
			raise PersistenceError(f"Failed to save history: {error}") from error

	def load_history(self, file_path: str | Path | None = None) -> None:
		target = Path(file_path) if file_path else self.history_file
		if not target.exists():
			self._log_event("history_load_missing_file", target=target)
			raise PersistenceError("History file not found.")

		try:
			frame = pd.read_csv(target, encoding=self.default_encoding)
		except Exception as error:
			self._log_event("history_load_read_error", target=target, error=error)
			raise PersistenceError(f"Failed to read history file: {error}") from error

		required_columns = {"operation", "operand_1", "operand_2", "result", "timestamp"}
		if not required_columns.issubset(frame.columns):
			self._log_event("history_load_missing_columns", target=target)
			raise PersistenceError("History file is malformed: missing required columns.")

		try:
			calculations = [Calculation.from_dict(row) for _, row in frame.iterrows()]
		except Exception as error:
			self._log_event("history_load_invalid_rows", target=target, error=error)
			raise PersistenceError(f"History file contains invalid row data: {error}") from error

		self._caretaker.save_for_undo(self.history.get_all())
		self._caretaker.clear_redo()
		self.history.set_all(calculations)
		self._log_event("history_loaded", target=target, rows=len(calculations))

	def _format_calculation(self, calculation: Calculation) -> str:
		display_name = {
			"int_divide": "integer_divide",
			"percent": "percentage",
			"abs_diff": "absolute_difference",
		}.get(calculation.operation, calculation.operation)
		return f"{display_name}({calculation.operand_1}, {calculation.operand_2}) = {calculation.result}"

	@staticmethod
	def _help_message() -> str:
		return (
			"Available commands:\n"
			"  Operations: add, subtract, multiply, divide, power, root, modulus, int_divide, percent, abs_diff <a> <b>\n"
			"  History: history, clear, undo, redo\n"
			"  Persistence: save [file], load [file]\n"
			"  Other: help (or ?), exit"
		)

	def _handle_help(self, _parts: list[str], action: str) -> tuple[str, bool]:
		self._log_event("command_response", action=action, should_exit=False)
		return self._help_message(), False

	def _handle_exit(self, _parts: list[str], action: str) -> tuple[str, bool]:
		self._log_event("command_response", action=action, should_exit=True)
		return "Exiting calculator.", True

	def _handle_history(self, _parts: list[str], action: str) -> tuple[str, bool]:
		history = self.get_history()
		if not history:
			self._log_event("command_response", action=action, message="History is empty.", should_exit=False)
			return "History is empty.", False
		self._log_event("command_response", action=action, entries=len(history), should_exit=False)
		return "\n".join(self._format_calculation(item) for item in history), False

	def _handle_clear(self, _parts: list[str], action: str) -> tuple[str, bool]:
		self.clear_history()
		self._log_event("command_response", action=action, should_exit=False)
		return "History cleared.", False

	def _handle_undo(self, _parts: list[str], action: str) -> tuple[str, bool]:
		before = len(self.history.get_all())
		self.undo()
		after = len(self.history.get_all())
		self._log_event("command_response", action=action, before=before, after=after, should_exit=False)
		return ("Undo successful.", False) if before != after else ("Nothing to undo.", False)

	def _handle_redo(self, _parts: list[str], action: str) -> tuple[str, bool]:
		before = len(self.history.get_all())
		self.redo()
		after = len(self.history.get_all())
		self._log_event("command_response", action=action, before=before, after=after, should_exit=False)
		return ("Redo successful.", False) if before != after else ("Nothing to redo.", False)

	def _handle_save(self, parts: list[str], action: str) -> tuple[str, bool]:
		if len(parts) > 2:
			self._log_event("command_response", action=action, error="invalid_arguments", should_exit=False)
			return "Error: save accepts zero or one file path argument.", False

		path = parts[1] if len(parts) == 2 else None
		try:
			self.save_history(path)
			self._log_event("command_response", action=action, should_exit=False)
			return "History saved.", False
		except PersistenceError as error:
			self._log_event("command_response", action=action, error=error, should_exit=False)
			return f"Error: {error}", False

	def _handle_load(self, parts: list[str], action: str) -> tuple[str, bool]:
		if len(parts) > 2:
			self._log_event("command_response", action=action, error="invalid_arguments", should_exit=False)
			return "Error: load accepts zero or one file path argument.", False

		path = parts[1] if len(parts) == 2 else None
		try:
			self.load_history(path)
			self._log_event("command_response", action=action, should_exit=False)
			return "History loaded.", False
		except PersistenceError as error:
			self._log_event("command_response", action=action, error=error, should_exit=False)
			return f"Error: {error}", False

	def _handle_operation(self, parts: list[str], action: str) -> tuple[str, bool]:
		if len(parts) != 3:
			self._log_event("command_response", action=action, error="invalid_operands", should_exit=False)
			return "Operations require exactly two numeric operands.", False

		try:
			calculation = self.calculate(parts[0], parts[1], parts[2])
			self._log_event("command_response", action=action, should_exit=False)
			return self._format_calculation(calculation), False
		except CalculatorError as error:
			self._log_event("command_response", action=action, error=error, should_exit=False)
			return f"Error: {error}", False

	def run_command(self, command: str) -> tuple[str, bool]:
		parts = command.strip().split()
		self._log_event("command_received", command=command.strip())
		if not parts:
			self._log_event("command_response", message="Please enter a command.", should_exit=False)
			return "Please enter a command.", False

		action = parts[0].lower()
		handler = self._command_handlers.get(action)
		if handler is not None:
			return handler(parts, action)

		if action not in self._OPERATION_COMMANDS:
			self._log_event("command_response", action=action, error="unknown_command", should_exit=False)
			return f"Unknown command '{action}'. Type 'help' to view available commands.", False

		return self._handle_operation(parts, action)


@dataclass(frozen=True)
class ReplPresentationConfig:
	prompt: str = "calc> "
	welcome_message: str = "Calculator REPL started. Type 'help' for available commands."
	use_color: bool = True
	success_messages: set[str] = field(
		default_factory=lambda: {
			"History saved.",
			"History loaded.",
			"History cleared.",
		}
	)
	error_prefixes: tuple[str, ...] = ("Error:", "Unknown command")


class ReplMessageLevelStrategy:
	def __init__(self, config: ReplPresentationConfig | None = None):
		self.config = config or ReplPresentationConfig()

	def classify(self, message: str, should_exit: bool) -> str:
		if should_exit:
			return "warning"

		if message.startswith(self.config.error_prefixes):
			return "error"

		if "successful" in message or message in self.config.success_messages:
			return "success"

		return "info"


def colorize_output(text: str, level: str = "info", use_color: bool = True, color: str | None = None) -> str:
	if not use_color:
		return text

	try:
		from colorama import Fore, Style
	except ImportError:
		return text

	if color is not None:
		selected_color = color.lower()
	else:
		selected_color = {
			"success": "green",
			"error": "red",
			"warning": "yellow",
			"info": "cyan",
		}.get(level.lower(), "cyan")

	palette = {
		"green": Fore.GREEN,
		"red": Fore.RED,
		"yellow": Fore.YELLOW,
		"cyan": Fore.CYAN,
	}
	prefix = palette.get(selected_color, Fore.CYAN)
	return f"{prefix}{text}{Style.RESET_ALL}"


def run_command(calc: Calculator, command: str) -> str:
	message, should_exit = calc.run_command(command)
	if should_exit:
		return "exit"
	return message


def run_repl(
	calculator: Calculator | None = None,
	presentation_config: ReplPresentationConfig | None = None,
	level_strategy: ReplMessageLevelStrategy | None = None,
) -> None:
	calc = calculator or Calculator()
	config = presentation_config or ReplPresentationConfig()
	strategy = level_strategy or ReplMessageLevelStrategy(config)
	calc._log_event("repl_started")
	print(colorize_output(config.welcome_message, level="info", use_color=config.use_color))
	while True:
		try:
			command = input(colorize_output(config.prompt, level="info", use_color=config.use_color))
			message, should_exit = calc.run_command(command)
			level = strategy.classify(message, should_exit)
			print(colorize_output(message, level=level, use_color=config.use_color))
			if should_exit:
				calc._log_event("repl_stopped", reason="user_exit")
				break
		except EOFError:
			calc._log_event("repl_stopped", reason="eof")
			print(colorize_output("Exiting calculator.", level="warning", use_color=config.use_color))
			break
		except KeyboardInterrupt:
			calc._log_event("repl_stopped", reason="keyboard_interrupt")
			print(colorize_output("Exiting calculator.", level="warning", use_color=config.use_color))
			break
		except Exception as error:
			calc._log_event("repl_error", error=error)
			print(colorize_output(f"Error: {error}", level="error", use_color=config.use_color))


__all__ = [
	"Operation",
	"BinaryOperation",
	"UnaryOperation",
	"Add",
	"Subtract",
	"Multiply",
	"Divide",
	"Power",
	"Root",
	"Modulus",
	"IntegerDivide",
	"Percentage",
	"Absolute",
	"AbsoluteDifference",
	"OperationFactory",
	"Calculator",
	"ReplPresentationConfig",
	"ReplMessageLevelStrategy",
	"run_repl",
	"run_command",
	"colorize_output",
]
