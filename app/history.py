from app.calculation import Calculation


class HistoryManager:
	def __init__(self):
		self._items: list[Calculation] = []

	def add(self, calculation: Calculation) -> None:
		self._items.append(calculation)

	def get_all(self) -> list[Calculation]:
		return list(self._items)

	def clear(self) -> None:
		self._items.clear()
