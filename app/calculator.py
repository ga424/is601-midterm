from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable

import pandas as pd

from app.calculation import Calculation
from app.history import HistoryManager

""" Arithmetic Operations supporting Factory Design Pattern for a REPL application.
This module provides basic arithmetic operations through a factory pattern,
allowing dynamic operation selection and execution.
"""

class Operation(ABC):
    """Abstract base class for all operations."""
    
    @abstractmethod
    def execute(self, *args) -> float:
        """Execute the operation with given arguments."""
        pass


class BinaryOperation(Operation):
    """Base class for operations requiring two arguments."""
    
    def __init__(self, func: Callable):
        self.func = func
    
    def execute(self, x: float, y: float) -> float:
        return self.func(x, y)


class UnaryOperation(Operation):
    """Base class for operations requiring one argument."""
    
    def __init__(self, func: Callable):
        self.func = func
    
    def execute(self, x: float) -> float:
        return self.func(x)


# Binary Operations
class Add(BinaryOperation):
    def __init__(self):
        super().__init__(lambda x, y: x + y)


class Subtract(BinaryOperation):
    def __init__(self):
        super().__init__(lambda x, y: x - y)


class Multiply(BinaryOperation):
    def __init__(self):
        super().__init__(lambda x, y: x * y)


class Divide(BinaryOperation):
    def __init__(self):
        def divide_impl(x, y):
            if y == 0:
                raise ValueError("Cannot divide by zero.")
            return x / y
        super().__init__(divide_impl)


class Power(BinaryOperation):
    def __init__(self):
        super().__init__(lambda x, y: x ** y)


class Root(BinaryOperation):
    def __init__(self):
        def root_impl(x, y):
            if y == 0:
                raise ValueError("Cannot take the root with degree zero.")
            return x ** (1 / y)
        super().__init__(root_impl)


class Modulus(BinaryOperation):
    def __init__(self):
        def modulus_impl(x, y):
            if y == 0:
                raise ValueError("Cannot take modulus with zero.")
            return x % y
        super().__init__(modulus_impl)


class IntegerDivide(BinaryOperation):
    def __init__(self):
        def int_divide_impl(x, y):
            if y == 0:
                raise ValueError("Cannot perform integer division by zero.")
            return int(x // y)
        super().__init__(int_divide_impl)


class Percentage(BinaryOperation):
    def __init__(self):
        def percentage_impl(x, y):
            if y == 0:
                raise ValueError("Cannot calculate percentage with zero as denominator.")
            return (x / y) * 100
        super().__init__(percentage_impl)


# Unary Operations
class Absolute(UnaryOperation):
    def __init__(self):
        super().__init__(lambda x: abs(x))

class AbsoluteDifference(BinaryOperation):
    def __init__(self):
        super().__init__(lambda x, y: abs(x - y))

class OperationFactory:
    """Factory for creating operation objects."""
    
    """ Mapping of operation names to their corresponding classes """
    _operations = {
        'add': Add,
        'subtract': Subtract,
        'multiply': Multiply,
        'divide': Divide,
        'power': Power,
        'root': Root,
        'modulus': Modulus,
        'integer_divide': IntegerDivide,
        'percentage': Percentage,
        'absolute': Absolute,
        'absolute_difference': AbsoluteDifference
    }
    
    @classmethod
    def create_operation(cls, operation_name: str) -> Operation:
        """Create and return an operation instance."""
        if operation_name not in cls._operations:
            raise ValueError(f"Unknown operation: {operation_name}. Available operations: {', '.join(cls.get_available_operations())}")
        return cls._operations[operation_name]()
    
    @classmethod
    def get_available_operations(cls) -> list:
        """Return list of available operations."""
        return list(cls._operations.keys())


class Calculator:
    _operation_aliases = {
        "int_divide": "integer_divide",
        "percent": "percentage",
        "abs_diff": "absolute_difference",
    }

    _system_commands = {"history", "clear", "undo", "redo", "save", "load", "help", "exit"}

    def __init__(self, history_file: str = "history.csv"):
        self.history = HistoryManager()
        self._undo_stack: list[list[Calculation]] = []
        self._redo_stack: list[list[Calculation]] = []
        self.history_file = history_file

    def _resolve_operation(self, command_name: str) -> str:
        return self._operation_aliases.get(command_name, command_name)

    def _save_snapshot_for_undo(self) -> None:
        self._undo_stack.append(self.history.get_all())

    def _format_calculation(self, calculation: Calculation) -> str:
        return (
            f"{calculation.operation}({calculation.operand_1}, {calculation.operand_2}) = {calculation.result}"
        )

    def calculate(self, command_name: str, operand_1: float, operand_2: float) -> Calculation:
        operation_name = self._resolve_operation(command_name)
        operation = OperationFactory.create_operation(operation_name)
        result = operation.execute(operand_1, operand_2)
        calculation = Calculation(operation_name, operand_1, operand_2, result)

        self._save_snapshot_for_undo()
        self.history.add(calculation)
        self._redo_stack.clear()
        return calculation

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

    def clear_history(self) -> None:
        self._save_snapshot_for_undo()
        self.history.clear()
        self._redo_stack.clear()

    def save_history(self, file_path: str | None = None) -> None:
        target = Path(file_path or self.history_file)
        target.parent.mkdir(parents=True, exist_ok=True)
        rows = [item.to_dict() for item in self.history.get_all()]
        frame = pd.DataFrame(rows, columns=["operation", "operand_1", "operand_2", "result", "timestamp"])
        frame.to_csv(target, index=False)

    def load_history(self, file_path: str | None = None) -> None:
        target = Path(file_path or self.history_file)
        if not target.exists():
            raise ValueError(f"History file not found: {target}")

        frame = pd.read_csv(target)
        required_columns = {"operation", "operand_1", "operand_2", "result", "timestamp"}
        if not required_columns.issubset(set(frame.columns)):
            raise ValueError("History file is malformed.")

        loaded = [Calculation.from_dict(row) for row in frame.to_dict(orient="records")]
        self._save_snapshot_for_undo()
        self.history.set_all(loaded)
        self._redo_stack.clear()

    def _help_text(self) -> str:
        commands = [
            "add", "subtract", "multiply", "divide", "power", "root", "modulus", "int_divide", "percent", "abs_diff",
            "history", "clear", "undo", "redo", "save", "load", "help", "exit",
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
                path = args[0] if args else None
                self.save_history(path)
                return "History saved.", False
            if command == "load":
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
        except ValueError as error:
            return f"Error: {error}", False


def run_repl(calculator: Calculator | None = None) -> None:
    calculator = calculator or Calculator()
    while True:
        user_input = input("calc> ")
        message, should_exit = calculator.run_command(user_input)
        print(message)
        if should_exit:
            break
