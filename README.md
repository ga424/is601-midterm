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

## Configuration (.env)

Create a local `.env` file from the example and adjust values as needed:

```bash
cp .env.example .env
```

Supported configuration keys:

- `CALCULATOR_LOG_DIR`
- `CALCULATOR_HISTORY_DIR`
- `CALCULATOR_LOG_FILE`
- `CALCULATOR_LOG_LEVEL` (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`; default `INFO`)
- `CALCULATOR_HISTORY_FILE`
- `CALCULATOR_MAX_HISTORY_SIZE`
- `CALCULATOR_AUTO_SAVE`
- `CALCULATOR_PRECISION`
- `CALCULATOR_MAX_INPUT_VALUE`
- `CALCULATOR_DEFAULT_ENCODING`
- `CALCULATOR_REPL_PROMPT`
- `CALCULATOR_REPL_WELCOME_MESSAGE`
- `CALCULATOR_REPL_USE_COLOR`

The application loads `.env` values on startup and uses defaults when a value is not set.

### REPL Customization Examples

Customize prompt and welcome message:

```dotenv
CALCULATOR_REPL_PROMPT=mycalc> 
CALCULATOR_REPL_WELCOME_MESSAGE=Welcome to My Calculator!
```

Disable color output (useful for plain terminals):

```dotenv
CALCULATOR_REPL_USE_COLOR=false
```

## Run Tests

```bash
pytest
```

## Run Lint

```bash
ruff check .
```

## Architecture (C4)

C4 architecture diagrams are available at [docs/c4-architecture.md](docs/c4-architecture.md), including:

- System Context (Level 1)
- Container Diagram (Level 2)
- Component Diagram for Calculator Core (Level 3)
- Code Summary View (module and test mapping)
- Deployment View (runtime and CI perspective)

For Mermaid preview/export instructions, see [docs/diagrams/README.md](docs/diagrams/README.md).

## Coverage Policy

This project enforces **100% test coverage** via `pytest-cov`.

- Local enforcement is configured in `pytest.ini`
- CI enforcement runs in GitHub Actions workflow `.github/workflows/tests.yml`

Any pull request or push to `main` fails if coverage drops below `100%`.

## Log Format

The calculator writes structured log entries to `calculator.log` with standardized fields:

- `time`: timestamp for the event
- `level`: log level (for example `INFO`)
- `logger`: logger name
- `class`: class that emitted the log event
- `message`: event payload in key-value form

Example:

```text
time=2026-03-06T22:14:03+0000 level=INFO logger=calculator.calculator.log class=Calculator message=event=command_received command=add 2 3
```

This makes logs easier to filter, parse, and audit during debugging and rubric review.

### Log Severity Policy

Use this policy for consistent event classification:

| Level | When to use | Examples |
|---|---|---|
| `INFO` | Normal successful flow and lifecycle events | `calculator_initialized`, `command_received`, `calculation_completed`, `history_saved`, `history_loaded`, `repl_started`, `repl_stopped` |
| `WARNING` | Expected but non-ideal outcomes or recoverable user issues | `undo_noop`, `redo_noop`, `history_load_missing_file`, `history_load_missing_columns`, unknown command, invalid command arguments |
| `ERROR` | Unexpected failures or operation/persistence exceptions | `calculation_error`, `calculation_domain_error`, `history_save_error`, `history_load_read_error`, `history_load_invalid_rows`, `repl_error` |

Default runtime level is `INFO` and can be configured via `CALCULATOR_LOG_LEVEL`.

## Feature Branch Workflow

Use a feature branch for every change, then open a pull request (merge request) into `main`.

```bash
git checkout main
git pull origin main
git checkout -b feature/<short-description>
# make changes
git add .
git commit -m "feat: describe change"
git push -u origin feature/<short-description>
```

Then open a Pull Request from `feature/<short-description>` (or `integration/<short-description>` when combining approved feature work) to `main`.

### Enforced in CI

- PR source branch must match `feature/<short-description>` or `integration/<short-description>`
- Tests must pass with `100%` coverage

### Required GitHub Repository Setting

In GitHub, enable branch protection for `main`:

- Require a pull request before merging
- Require status checks to pass before merging (`Tests`, `Branch Policy`)
- Optionally restrict direct pushes to `main`

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
