from dataclasses import dataclass, field
from datetime import datetime, timezone


# This module defines the Calculation data class, which represents a single calculation performed by the calculator.
# It allows us to have a structured way to store and manage the details of each calculation, including the operation, operands, result, and timestamp.
@dataclass(frozen=True)
class Calculation:
	operation: str
	operand_1: float
	operand_2: float
	result: float
	timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

	#This is an instance method that converts the Calculation object into a dictionary format, making it easier to serialize and store the calculation details.
	def to_dict(self) -> dict:
		return {
			"operation": self.operation,
			"operand_1": self.operand_1,
			"operand_2": self.operand_2,
			"result": self.result,
			"timestamp": self.timestamp.isoformat(),
		}
    # This is a class method that enables us to create a Calculation instance from a dictionary.
	@classmethod
	def from_dict(cls, payload: dict) -> "Calculation":
		return cls(
			operation=str(payload["operation"]),
			operand_1=float(payload["operand_1"]),
			operand_2=float(payload["operand_2"]),
			result=float(payload["result"]),
			timestamp=datetime.fromisoformat(str(payload["timestamp"])),
		)
