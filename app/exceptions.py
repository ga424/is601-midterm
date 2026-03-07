class CalculatorError(Exception):
	"""Base calculator exception."""


class PersistenceError(CalculatorError):
	"""Raised when history persistence fails."""
