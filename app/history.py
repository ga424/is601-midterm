from app.calculation import Calculation


class HistoryManager:
	def __init__(self):
		self._history: list[Calculation] = []

	def add(self, calculation: Calculation) -> None:
		self._history.append(calculation)

	def clear(self) -> None:
		self._history.clear()

	def get_all(self) -> list[Calculation]:
		return list(self._history)

	def set_all(self, calculations: list[Calculation]) -> None:
		self._history = list(calculations)
