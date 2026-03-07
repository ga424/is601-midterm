from app.calculation import Calculation


class HistoryManager:
	def __init__(self, max_size: int = 100):
		if max_size <= 0:
			raise ValueError("max_size must be greater than zero.")
		self.max_size = max_size
		self._items: list[Calculation] = []

	def add(self, calculation: Calculation) -> None:
		self._items.append(calculation)
		while len(self._items) > self.max_size:
			self._items.pop(0)

	def clear(self) -> None:
		self._items.clear()

	def get_all(self) -> list[Calculation]:
		return list(self._items)

	def set_all(self, calculations: list[Calculation]) -> None:
		self._items = list(calculations)[-self.max_size :]

	def last(self) -> Calculation | None:
		if not self._items:
			return None
		return self._items[-1]
