from pathlib import Path

import pandas as pd

from app.calculation import Calculation
from app.exceptions import PersistenceError
from app.history import HistoryManager
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
]


class Calculator:
    _operation_aliases = {
        "int_divide": "integer_divide",
        "percent": "percentage",
        "abs_diff": "absolute_difference",
    }

    _system_commands = {"history", "clear", "undo", "redo", "save", "load", "help", "exit"}

    def __init__(self, history_file: str = "history.csv"):
        self.history = HistoryManager()
        self._observers = []
        self._undo_stack: list[list[Calculation]] = []
        self._redo_stack: list[list[Calculation]] = []
        self.history_file = history_file

    def register_observer(self, observer) -> None:
        self._observers.append(observer)

    def unregister_observer(self, observer) -> None:
        if observer in self._observers:
            self._observers.remove(observer)

    def _notify_observers(self, calculation: Calculation) -> None:
        for observer in self._observers:
            observer.update(calculation)

    def _resolve_operation(self, command_name: str) -> str:
        return self._operation_aliases.get(command_name, command_name)

    def _save_snapshot_for_undo(self) -> None:
        self._undo_stack.append(self.history.get_all())

    def _format_calculation(self, calculation: Calculation) -> str:
        return f"{calculation.operation}({calculation.operand_1}, {calculation.operand_2}) = {calculation.result}"

    def calculate(self, operation_name: str, operand_1: float, operand_2: float) -> Calculation:
        resolved_operation = self._resolve_operation(operation_name)
        operation = OperationFactory.create_operation(resolved_operation)
        result = operation.execute(operand_1, operand_2)
        calculation = Calculation(resolved_operation, operand_1, operand_2, result)

        self._save_snapshot_for_undo()
        self.history.add(calculation)
        self._redo_stack.clear()
        self._notify_observers(calculation)
        return calculation

    def get_history(self) -> list[Calculation]:
        return self.history.get_all()

    def clear_history(self) -> None:
        self._save_snapshot_for_undo()
        self.history.clear()
        self._redo_stack.clear()

    def undo(self) -> bool:
        if not self._undo_stack:
            return False
        self._redo_stack.append(self.history.get_all())
        self.history.set_all(self._undo_stack.pop())
        return True

    def redo(self) -> bool:
        if not self._redo_stack:
            return False
        self._undo_stack.append(self.history.get_all())
        self.history.set_all(self._redo_stack.pop())
        return True

    def save_history(self, file_path: str | None = None) -> None:
        target = Path(file_path or self.history_file)
        target.parent.mkdir(parents=True, exist_ok=True)
        rows = [item.to_dict() for item in self.history.get_all()]
        dataframe = pd.DataFrame(rows, columns=["operation", "operand_1", "operand_2", "result", "timestamp"])
        try:
            dataframe.to_csv(target, index=False)
        except (OSError, ValueError) as error:
            raise PersistenceError(f"Failed to save history to '{target}'.") from error

    def load_history(self, file_path: str | None = None) -> None:
        target = Path(file_path or self.history_file)
        if not target.exists():
            raise PersistenceError(f"History file not found: '{target}'.")

        try:
            dataframe = pd.read_csv(target)
        except (OSError, ValueError, pd.errors.ParserError) as error:
            raise PersistenceError(f"Failed to read history file '{target}'.") from error

        required_columns = {"operation", "operand_1", "operand_2", "result", "timestamp"}
        if not required_columns.issubset(set(dataframe.columns)):
            raise PersistenceError("History file is malformed: missing required columns.")

        try:
            loaded_history = [Calculation.from_dict(row) for row in dataframe.to_dict(orient="records")]
        except (KeyError, TypeError, ValueError) as error:
            raise PersistenceError("History file contains invalid row data.") from error

        self._save_snapshot_for_undo()
        self.history.set_all(loaded_history)
        self._redo_stack.clear()

    def _help_text(self) -> str:
        commands = [
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
            "history",
            "clear",
            "undo",
            "redo",
            "save",
            "load",
            "help",
            "exit",
        ]
        return "Available commands: " + ", ".join(commands)

    def run_command(self, raw_command: str) -> tuple[str, bool]:
        parts = raw_command.strip().split()
        if not parts:
            return "Please enter a command.", False

        command = parts[0].lower()
        args = parts[1:]

        try:
            if command == "exit":
                return "Exiting calculator.", True
            if command == "help":
                return self._help_text(), False
            if command == "history":
                history = self.history.get_all()
                if not history:
                    return "History is empty.", False
                return "\n".join(self._format_calculation(item) for item in history), False
            if command == "clear":
                self.clear_history()
                return "History cleared.", False
            if command == "undo":
                return ("Undo successful." if self.undo() else "Nothing to undo."), False
            if command == "redo":
                return ("Redo successful." if self.redo() else "Nothing to redo."), False
            if command == "save":
                if len(args) > 1:
                    return "Error: save accepts zero or one file path argument.", False
                path = args[0] if args else None
                self.save_history(path)
                return "History saved.", False
            if command == "load":
                if len(args) > 1:
                    return "Error: load accepts zero or one file path argument.", False
                path = args[0] if args else None
                self.load_history(path)
                return "History loaded.", False

            if command in self._system_commands:
                return f"Unknown command usage for '{command}'.", False

            if len(args) != 2:
                return "Operations require exactly two numeric operands.", False

            operand_1 = float(args[0])
            operand_2 = float(args[1])
            calculation = self.calculate(command, operand_1, operand_2)
            return self._format_calculation(calculation), False
        except (ValueError, PersistenceError) as error:
            return f"Error: {error}", False


def run_repl(calculator: Calculator | None = None) -> None:
    calculator = calculator or Calculator()
    while True:
        user_input = input("calc> ")
        message, should_exit = calculator.run_command(user_input)
        print(message)
        if should_exit:
            break
