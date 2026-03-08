# C4 Architecture Diagrams

This document captures the calculator architecture using C4 model views.

> Important: use Markdown Preview for this file. Do not run Mermaid Preview on this `.md` file directly.

## Rendering Note

If you see an error like `Lexical error ... Unrecognized text. # C4 Architecture ...`, it means Mermaid Preview is parsing this whole Markdown file as Mermaid source.

Use one of the standalone Mermaid files in [docs/diagrams](docs/diagrams) for rendering/export:

- [docs/diagrams/c4-context.mmd](docs/diagrams/c4-context.mmd)
- [docs/diagrams/c4-container.mmd](docs/diagrams/c4-container.mmd)
- [docs/diagrams/c4-component-core.mmd](docs/diagrams/c4-component-core.mmd)
- [docs/diagrams/code-summary.mmd](docs/diagrams/code-summary.mmd)
- [docs/diagrams/deployment-view.mmd](docs/diagrams/deployment-view.mmd)

Quick steps in VS Code:

1. Open one `.mmd` file from the list above.
2. Run `Mermaid: Open Preview` (or right-click → Mermaid Preview).

## Level 1 — System Context

```mermaid
C4Context
    title Calculator System Context
    Person(user, "Calculator User", "Runs calculator commands in a terminal")

    System(calculator, "IS601 Calculator", "Python CLI calculator application")
    System_Ext(filesystem, "Local Filesystem", "Stores calculator history and logs")
    System_Ext(environment, "Environment Variables", "Provides runtime configuration from .env")

    Rel(user, calculator, "Uses", "CLI commands")
    Rel(calculator, filesystem, "Reads/Writes", "CSV history, log files")
    Rel(calculator, environment, "Loads", "Configuration values")
```

## Level 2 — Container Diagram

```mermaid
C4Container
    title Calculator Container View
    Person(user, "Calculator User")

    System_Boundary(calc_app, "IS601 Calculator Application") {
        Container(cli, "CLI Entrypoint", "Python (main.py)", "Starts app, loads config, launches REPL")
        Container(core, "Calculator Core", "Python (app/calculator.py)", "Executes commands and operations, manages history")
        Container(config, "Configuration", "Python (app/calculator_config.py)", "Loads and validates env settings")
        Container(commands, "REPL Command Layer", "Python (app/repl_commands.py)", "Parses and dispatches REPL commands")
        Container(ops, "Operation Engine", "Python (app/operations.py)", "Factory and operation implementations")
        Container(persistence, "History + Logging", "Python (app/history.py, app/logger.py)", "Persists history and structured logs")
    }

    System_Ext(filesystem, "Local Filesystem", "history/*.csv, logs/*.log")

    Rel(user, cli, "Interacts with", "Terminal input/output")
    Rel(cli, config, "Loads")
    Rel(cli, core, "Creates and starts")
    Rel(core, commands, "Delegates command handling")
    Rel(commands, ops, "Invokes operation factory")
    Rel(core, persistence, "Stores and retrieves history/events")
    Rel(persistence, filesystem, "Reads/Writes")
```

## Level 3 — Component Diagram (Calculator Core)

```mermaid
C4Component
    title Calculator Core Components
    Container_Boundary(core, "Calculator Core (app/calculator.py)") {
        Component(repl, "REPL Loop", "run_repl", "Interactive command loop and message presentation")
        Component(dispatch, "Command Dispatch", "run_command + registry", "Routes text commands to handlers")
        Component(calc_service, "Calculation Service", "Calculator.calculate", "Validates input and computes results")
        Component(history_mgmt, "History Management", "HistoryManager + CalculatorCaretaker", "Tracks state and undo/redo")
        Component(observer_flow, "Observer Notifications", "LoggingObserver + AutoSaveObserver", "Publishes calculation events")
    }

    Component_Ext(config, "Config Loader", "app/calculator_config.py")
    Component_Ext(operations, "Operation Factory", "app/operations.py")
    Component_Ext(repl_cmds, "REPL Commands", "app/repl_commands.py")
    Component_Ext(storage, "Persistence", "CSV files + logs")

    Rel(repl, dispatch, "Sends commands")
    Rel(dispatch, repl_cmds, "Uses handlers")
    Rel(dispatch, calc_service, "Executes operations")
    Rel(calc_service, operations, "Creates operations")
    Rel(calc_service, history_mgmt, "Stores snapshots and calculations")
    Rel(calc_service, observer_flow, "Notifies observers")
    Rel(observer_flow, storage, "Writes logs/history")
    Rel(config, repl, "Provides REPL settings")
```

## Code Summary View

```mermaid
flowchart LR
    A[main.py\nEntrypoint] --> B[app/calculator_config.py\nEnvironment config]
    A --> C[app/calculator.py\nCalculator orchestration]

    C --> D[app/repl_commands.py\nCommand objects]
    C --> E[app/operations.py\nFactory + operations]
    C --> F[app/history.py\nHistoryManager]
    C --> G[app/calculator_memento.py\nUndo/Redo]
    C --> H[app/logger.py\nLogger + Observers]
    C --> I[app/input_validators.py\nValidation helpers]
    C --> J[app/calculation.py\nCalculation model]

    K[tests/test_config.py] --> B
    L[tests/test_calculator.py] --> C
    M[tests/test_repl.py] --> D
    N[tests/test_operations.py\n+ test_operations_classes.py] --> E
    O[tests/test_history.py] --> F
    P[tests/test_logger.py] --> H
    Q[tests/test_calculation.py] --> J
```

## Deployment View

```mermaid
flowchart TD
    U[User Terminal] --> APP[Calculator CLI Process\nPython 3.11+]

    subgraph Runtime[Local Runtime Environment]
        ENV[.env variables]
        APP
        HIST[history/history.csv]
        LOGS[logs/calculator.log]
    end

    ENV --> APP
    APP --> HIST
    APP --> LOGS

    GH[GitHub Actions CI] --> TESTS[pytest + coverage gate]
    GH --> LINT[ruff lint gate]
```
