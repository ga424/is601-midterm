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

    def get_history(self) -> list[Calculation]:
        return self.history.get_all()

    def clear_history(self) -> None:
        self.history.clear()

    def save_history(self, file_path: str) -> None:
        rows = [item.to_dict() for item in self.history.get_all()]
        dataframe = pd.DataFrame(rows, columns=["operation", "operand_1", "operand_2", "result", "timestamp"])
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            dataframe.to_csv(path, index=False)
        except (OSError, ValueError) as error:
            raise PersistenceError(f"Failed to save history to '{file_path}'.") from error

    def load_history(self, file_path: str) -> None:
        path = Path(file_path)
        if not path.exists():
            raise PersistenceError(f"History file not found: '{file_path}'.")

        try:
            dataframe = pd.read_csv(path)
        except (OSError, ValueError, pd.errors.ParserError) as error:
            raise PersistenceError(f"Failed to read history file '{file_path}'.") from error

        required_columns = {"operation", "operand_1", "operand_2", "result", "timestamp"}
        if not required_columns.issubset(set(dataframe.columns)):
            raise PersistenceError("History file is malformed: missing required columns.")

        try:
            loaded_history = [Calculation.from_dict(row) for row in dataframe.to_dict(orient="records")]
        except (KeyError, TypeError, ValueError) as error:
            raise PersistenceError("History file contains invalid row data.") from error

        self.history.set_all(loaded_history)
