# IS601 Midterm Calculator

[![Tests](https://github.com/ga424/is601-midterm/actions/workflows/tests.yml/badge.svg)](https://github.com/ga424/is601-midterm/actions/workflows/tests.yml)

Python calculator project using operation classes and a factory pattern.

## Requirements

- Python 3.11+
- `pip`

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Run Tests

```bash
pytest
```

## Coverage Policy

This project enforces **100% test coverage** via `pytest-cov`.

- Local enforcement is configured in `pytest.ini`
- CI enforcement runs in GitHub Actions workflow `.github/workflows/tests.yml`

Any pull request or push to `main` fails if coverage drops below `100%`.

## Available Operations

- add
- subtract
- multiply
- divide
- power
- root
- modulus
- integer_divide
- percentage
- absolute
- absolute_difference

## Example Usage

```python
from app.calculator import OperationFactory

# Binary operation
add = OperationFactory.create_operation("add")
print(add.execute(10, 5))  # 15

# Unary operation
absolute = OperationFactory.create_operation("absolute")
print(absolute.execute(-42))  # 42
```

```python
from app.calculator import OperationFactory

try:
	divide = OperationFactory.create_operation("divide")
	divide.execute(10, 0)
except ValueError as error:
	print(error)  # Cannot divide by zero.
```
