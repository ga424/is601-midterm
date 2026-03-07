from abc import ABC, abstractmethod
from typing import Callable

from app.calculation import Calculation
from app.calculator_memento import CalculatorCaretaker
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
    def __init__(self, max_history_size: int = 100):
        self.history = HistoryManager(max_size=max_history_size)
        self._caretaker = CalculatorCaretaker()

    def calculate(self, operation_name: str, operand_1: float, operand_2: float) -> Calculation:
        operation = OperationFactory.create_operation(operation_name)
        result = operation.execute(operand_1, operand_2)
        calculation = Calculation(
            operation=operation_name,
            operand_1=operand_1,
            operand_2=operand_2,
            result=result,
        )

        self._caretaker.save_for_undo(self.history.get_all())
        self.history.add(calculation)
        self._caretaker.clear_redo()
        return calculation

    def undo(self) -> bool:
        previous_state = self._caretaker.undo(self.history.get_all())
        if previous_state is None:
            return False
        self.history.set_all(previous_state)
        return True

    def redo(self) -> bool:
        next_state = self._caretaker.redo(self.history.get_all())
        if next_state is None:
            return False
        self.history.set_all(next_state)
        return True

    def clear_history(self) -> None:
        self._caretaker.save_for_undo(self.history.get_all())
        self.history.clear()
        self._caretaker.clear_redo()
