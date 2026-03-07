from dataclasses import dataclass

from app.calculation import Calculation


@dataclass(frozen=True)
class CalculatorMemento:
	state: tuple[Calculation, ...]


class CalculatorCaretaker:
	def __init__(self):
		self._undo_stack: list[CalculatorMemento] = []
		self._redo_stack: list[CalculatorMemento] = []

	@staticmethod
	def _snapshot(history: list[Calculation]) -> CalculatorMemento:
		return CalculatorMemento(tuple(history))

	def save_for_undo(self, history: list[Calculation]) -> None:
		self._undo_stack.append(self._snapshot(history))

	def clear_redo(self) -> None:
		self._redo_stack.clear()

	def undo(self, current_history: list[Calculation]) -> list[Calculation] | None:
		if not self._undo_stack:
			return None
		self._redo_stack.append(self._snapshot(current_history))
		previous_state = self._undo_stack.pop()
		return list(previous_state.state)

	def redo(self, current_history: list[Calculation]) -> list[Calculation] | None:
		if not self._redo_stack:
			return None
		self._undo_stack.append(self._snapshot(current_history))
		next_state = self._redo_stack.pop()
		return list(next_state.state)
