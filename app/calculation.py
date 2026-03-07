from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class Calculation:
	operation: str
	operand_1: float
	operand_2: float
	result: float
	timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

	def to_dict(self) -> dict:
		return {
			"operation": self.operation,
			"operand_1": self.operand_1,
			"operand_2": self.operand_2,
			"result": self.result,
			"timestamp": self.timestamp.isoformat(),
		}
