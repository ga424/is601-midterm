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

from app.calculation import Calculation
from app.history import HistoryManager

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
]


class Calculator:
    def __init__(self):
        self.history = HistoryManager()
        self._observers = []

    def register_observer(self, observer) -> None:
        self._observers.append(observer)

    def unregister_observer(self, observer) -> None:
        if observer in self._observers:
            self._observers.remove(observer)

    def _notify_observers(self, calculation: Calculation) -> None:
        for observer in self._observers:
            observer.update(calculation)

    def calculate(self, operation_name: str, operand_1: float, operand_2: float) -> Calculation:
        operation = OperationFactory.create_operation(operation_name)
        result = operation.execute(operand_1, operand_2)
        calculation = Calculation(operation_name, operand_1, operand_2, result)
        self.history.add(calculation)
        self._notify_observers(calculation)
        return calculation
