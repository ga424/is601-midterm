class CalculatorError(Exception):
	"""Base exception for calculator-related errors."""


class OperationError(CalculatorError):
	"""Raised when an operation cannot be executed."""


class DivideByZeroError(OperationError):
	"""Raised when an operation attempts to divide by zero."""


class ValidationError(CalculatorError):
	"""Raised when user input fails validation."""


class PersistenceError(CalculatorError):
	"""Raised when loading or saving calculator data fails."""
