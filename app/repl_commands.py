from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from app.exceptions import CalculatorError, PersistenceError

if TYPE_CHECKING:
	from app.calculator import Calculator


OPERATION_COMMANDS = {
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


class ReplCommand(ABC):
	@abstractmethod
	def execute(self, calculator: Calculator, parts: list[str], action: str) -> tuple[str, bool]:
		raise NotImplementedError  # pragma: no cover


class HelpCommand(ReplCommand):
	def execute(self, calculator: Calculator, _parts: list[str], action: str) -> tuple[str, bool]:
		calculator._log_event("command_response", action=action, should_exit=False)
		return calculator._help_message(), False


class ExitCommand(ReplCommand):
	def execute(self, calculator: Calculator, _parts: list[str], action: str) -> tuple[str, bool]:
		calculator._log_event("command_response", action=action, should_exit=True)
		return "Exiting calculator.", True


class HistoryCommand(ReplCommand):
	def execute(self, calculator: Calculator, _parts: list[str], action: str) -> tuple[str, bool]:
		history = calculator.get_history()
		if not history:
			calculator._log_event("command_response", action=action, message="History is empty.", should_exit=False)
			return "History is empty.", False
		calculator._log_event("command_response", action=action, entries=len(history), should_exit=False)
		return "\n".join(calculator._format_calculation(item) for item in history), False


class ClearCommand(ReplCommand):
	def execute(self, calculator: Calculator, _parts: list[str], action: str) -> tuple[str, bool]:
		calculator.clear_history()
		calculator._log_event("command_response", action=action, should_exit=False)
		return "History cleared.", False


class UndoCommand(ReplCommand):
	def execute(self, calculator: Calculator, _parts: list[str], action: str) -> tuple[str, bool]:
		before = len(calculator.history.get_all())
		calculator.undo()
		after = len(calculator.history.get_all())
		calculator._log_event("command_response", action=action, before=before, after=after, should_exit=False)
		return ("Undo successful.", False) if before != after else ("Nothing to undo.", False)


class RedoCommand(ReplCommand):
	def execute(self, calculator: Calculator, _parts: list[str], action: str) -> tuple[str, bool]:
		before = len(calculator.history.get_all())
		calculator.redo()
		after = len(calculator.history.get_all())
		calculator._log_event("command_response", action=action, before=before, after=after, should_exit=False)
		return ("Redo successful.", False) if before != after else ("Nothing to redo.", False)


class SaveCommand(ReplCommand):
	def execute(self, calculator: Calculator, parts: list[str], action: str) -> tuple[str, bool]:
		if len(parts) > 2:
			calculator._log_event("command_response", action=action, error="invalid_arguments", should_exit=False)
			return "Error: save accepts zero or one file path argument.", False

		path = parts[1] if len(parts) == 2 else None
		try:
			calculator.save_history(path)
			calculator._log_event("command_response", action=action, should_exit=False)
			return "History saved.", False
		except PersistenceError as error:
			calculator._log_event("command_response", action=action, error=error, should_exit=False)
			return f"Error: {error}", False


class LoadCommand(ReplCommand):
	def execute(self, calculator: Calculator, parts: list[str], action: str) -> tuple[str, bool]:
		if len(parts) > 2:
			calculator._log_event("command_response", action=action, error="invalid_arguments", should_exit=False)
			return "Error: load accepts zero or one file path argument.", False

		path = parts[1] if len(parts) == 2 else None
		try:
			calculator.load_history(path)
			calculator._log_event("command_response", action=action, should_exit=False)
			return "History loaded.", False
		except PersistenceError as error:
			calculator._log_event("command_response", action=action, error=error, should_exit=False)
			return f"Error: {error}", False


class OperationCommand(ReplCommand):
	def execute(self, calculator: Calculator, parts: list[str], action: str) -> tuple[str, bool]:
		if len(parts) != 3:
			calculator._log_event("command_response", action=action, error="invalid_operands", should_exit=False)
			return "Operations require exactly two numeric operands.", False

		try:
			calculation = calculator.calculate(parts[0], parts[1], parts[2])
			calculator._log_event("command_response", action=action, should_exit=False)
			return calculator._format_calculation(calculation), False
		except CalculatorError as error:
			calculator._log_event("command_response", action=action, error=error, should_exit=False)
			return f"Error: {error}", False


def build_command_registry() -> dict[str, ReplCommand]:
	return {
		"help": HelpCommand(),
		"?": HelpCommand(),
		"exit": ExitCommand(),
		"quit": ExitCommand(),
		"history": HistoryCommand(),
		"clear": ClearCommand(),
		"undo": UndoCommand(),
		"redo": RedoCommand(),
		"save": SaveCommand(),
		"load": LoadCommand(),
	}