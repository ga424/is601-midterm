import logging
from pathlib import Path

import pandas as pd

from app.calculation import Calculation
from app.history import HistoryManager


class Logger:
	def __init__(self, log_file: str | Path = "calculator.log"):
		self._logger = logging.getLogger(f"calculator.{Path(log_file)}")
		self._logger.setLevel(logging.INFO)
		self._logger.propagate = False
		if not self._logger.handlers:
			handler = logging.FileHandler(log_file, encoding="utf-8")
			handler.setFormatter(
				logging.Formatter(
					"time=%(asctime)s level=%(levelname)s logger=%(name)s class=%(class_name)s message=%(message)s",
					datefmt="%Y-%m-%dT%H:%M:%S%z",
				)
			)
			self._logger.addHandler(handler)

	def info(self, message: str, class_name: str = "Logger") -> None:
		self._logger.info(message, extra={"class_name": class_name})

	def event(self, event: str, class_name: str, **details) -> None:
		payload = " ".join(f"{key}={value}" for key, value in details.items())
		message = f"event={event}" if not payload else f"event={event} {payload}"
		self.info(message, class_name=class_name)


class LoggingObserver:
	def __init__(self, logger: Logger | None = None):
		self.logger = logger or Logger()

	def update(self, calculation: Calculation) -> None:
		self.logger.info(
			f"operation={calculation.operation} operands=({calculation.operand_1}, {calculation.operand_2}) result={calculation.result}",
			class_name=self.__class__.__name__,
		)


class AutoSaveObserver:
	def __init__(self, history: HistoryManager, csv_file: str | Path = "history.csv", enabled: bool = True):
		self.history = history
		self.csv_file = Path(csv_file)
		self.enabled = enabled

	def update(self, _: Calculation) -> None:
		if not self.enabled:
			return
		self.save()

	def save(self) -> None:
		rows = [item.to_dict() for item in self.history.get_all()]
		frame = pd.DataFrame(rows)
		self.csv_file.parent.mkdir(parents=True, exist_ok=True)
		frame.to_csv(self.csv_file, index=False)
