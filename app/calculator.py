from pathlib import Path

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
	def __init__(
		self,
		history_file: str | Path = "history.csv",
		max_history_size: int = 100,
		log_file: str | Path = "calculator.log",
	):
		self.history = HistoryManager(max_size=max_history_size)
		self.history_file = Path(history_file)
		self.log_file = Path(log_file)
		self._caretaker = CalculatorCaretaker()
		self._observers = []
		self._event_logger = Logger(log_file=self.log_file)
		self.register_observer(LoggingObserver(Logger(log_file=self.log_file)))
		self.register_observer(AutoSaveObserver(history=self.history, csv_file=self.history_file, enabled=True))
		self._log_event(
			"calculator_initialized",
			history_file=self.history_file,
			log_file=self.log_file,
			max_history_size=max_history_size,
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
			validated_left, validated_right = validate_two_numbers(left, right)
			operation = OperationFactory.create_operation(normalized)
			result = operation.execute(validated_left, validated_right)
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
			frame.to_csv(target, index=False)
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
			frame = pd.read_csv(target)
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

	def run_command(self, command: str) -> tuple[str, bool]:
		parts = command.strip().split()
		self._log_event("command_received", command=command.strip())
		if not parts:
			self._log_event("command_response", message="Please enter a command.", should_exit=False)
			return "Please enter a command.", False

		action = parts[0].lower()

		if action == "help":
			self._log_event("command_response", action=action, should_exit=False)
			return (
				"Available commands: add/subtract/multiply/divide/power/root/modulus/int_divide/percent/abs_diff <a> <b>, "
				"history, undo, redo, save [file], load [file], clear, exit",
				False,
			)

		if action in {"exit", "quit"}:
			self._log_event("command_response", action=action, should_exit=True)
			return "Exiting calculator.", True

		if action == "history":
			history = self.get_history()
			if not history:
				self._log_event("command_response", action=action, message="History is empty.", should_exit=False)
				return "History is empty.", False
			self._log_event("command_response", action=action, entries=len(history), should_exit=False)
			return "\n".join(self._format_calculation(item) for item in history), False

		if action == "clear":
			self.clear_history()
			self._log_event("command_response", action=action, should_exit=False)
			return "History cleared.", False

		if action == "undo":
			before = len(self.history.get_all())
			self.undo()
			after = len(self.history.get_all())
			self._log_event("command_response", action=action, before=before, after=after, should_exit=False)
			return ("Undo successful.", False) if before != after else ("Nothing to undo.", False)

		if action == "redo":
			before = len(self.history.get_all())
			self.redo()
			after = len(self.history.get_all())
			self._log_event("command_response", action=action, before=before, after=after, should_exit=False)
			return ("Redo successful.", False) if before != after else ("Nothing to redo.", False)

		if action == "save":
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

		if action == "load":
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


def run_repl(calculator: Calculator | None = None) -> None:
	calc = calculator or Calculator()
	calc._log_event("repl_started")
	while True:
		try:
			command = input("> ")
			message, should_exit = calc.run_command(command)
			print(message)
			if should_exit:
				calc._log_event("repl_stopped", reason="user_exit")
				break
		except KeyboardInterrupt:
			calc._log_event("repl_stopped", reason="keyboard_interrupt")
			print("Exiting calculator.")
			break
		except Exception as error:
			calc._log_event("repl_error", error=error)
			print(f"Error: {error}")


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
	"run_repl",
	"run_command",
	"colorize_output",
]
