from pathlib import Path

from app.calculator import Calculator, ReplMessageLevelStrategy, ReplPresentationConfig, colorize_output, run_repl
from app.exceptions import PersistenceError


def test_run_command_flow_and_messages(tmp_path):
	calculator = Calculator(history_file=tmp_path / "history.csv")

	message, should_exit = calculator.run_command("   ")
	assert message == "Please enter a command."
	assert should_exit is False

	help_message, _ = calculator.run_command("help")
	assert "Available commands" in help_message

	redo_message, _ = calculator.run_command("redo")
	assert redo_message == "Nothing to redo."

	op_message, _ = calculator.run_command("int_divide 10 3")
	assert op_message == "integer_divide(10.0, 3.0) = 3"

	history_message, _ = calculator.run_command("history")
	assert "integer_divide(10.0, 3.0) = 3" in history_message

	undo_message, _ = calculator.run_command("undo")
	assert undo_message == "Undo successful."

	redo_message2, _ = calculator.run_command("redo")
	assert redo_message2 == "Redo successful."

	save_message, _ = calculator.run_command("save")
	assert save_message == "History saved."

	load_message, _ = calculator.run_command("load")
	assert load_message == "History loaded."

	clear_message, _ = calculator.run_command("clear")
	assert clear_message == "History cleared."

	exit_message, should_exit = calculator.run_command("exit")
	assert exit_message == "Exiting calculator."
	assert should_exit is True


def test_run_command_usage_and_error_messages(tmp_path):
	calculator = Calculator(history_file=tmp_path / "history.csv")
	message, _ = calculator.run_command("add 10")
	assert message == "Operations require exactly two numeric operands."

	message, _ = calculator.run_command("foobar")
	assert message == "Unknown command 'foobar'. Type 'help' to view available commands."

	message, _ = calculator.run_command("?")
	assert "Available commands" in message

	message, _ = calculator.run_command("save a b")
	assert message == "Error: save accepts zero or one file path argument."

	message, _ = calculator.run_command("load a b")
	assert message == "Error: load accepts zero or one file path argument."

	message, _ = calculator.run_command("add one two")
	assert message.startswith("Error:")


def test_run_command_history_empty_and_path_based_save_load(tmp_path):
	calculator = Calculator(history_file=tmp_path / "default.csv")
	message, _ = calculator.run_command("history")
	assert message == "History is empty."

	calculator.run_command("add 1 2")
	file_path = tmp_path / "named.csv"
	message, _ = calculator.run_command(f"save {file_path}")
	assert message == "History saved."
	calculator.run_command("clear")
	message, _ = calculator.run_command(f"load {file_path}")
	assert message == "History loaded."


def test_run_command_returns_error_on_persistence_failure(tmp_path):
	calculator = Calculator(history_file=tmp_path / "missing.csv")
	message, _ = calculator.run_command("load")
	assert message.startswith("Error: History file not found")


def test_run_command_save_returns_error_on_persistence_failure(tmp_path, monkeypatch):
	calculator = Calculator(history_file=tmp_path / "history.csv")

	def broken_save(_path=None):
		raise PersistenceError("save failed")

	monkeypatch.setattr(calculator, "save_history", broken_save)
	message, _ = calculator.run_command("save bad.csv")
	assert message == "Error: save failed"


def test_run_repl_exits_when_exit_command_received(monkeypatch, capsys):
	calculator = Calculator(history_file=Path("history.csv"), log_file=Path("calculator.log"))
	inputs = iter(["help", "exit"])
	monkeypatch.setattr("builtins.input", lambda _prompt: next(inputs))

	run_repl(calculator)

	output = capsys.readouterr().out
	assert "Available commands" in output
	assert "Exiting calculator." in output


def test_run_repl_logs_start_and_stop_events(monkeypatch, tmp_path):
	log_file = tmp_path / "events.log"
	calculator = Calculator(history_file=tmp_path / "history.csv", log_file=log_file)
	inputs = iter(["exit"])
	monkeypatch.setattr("builtins.input", lambda _prompt: next(inputs))

	run_repl(calculator)

	content = log_file.read_text(encoding="utf-8")
	assert "event=repl_started" in content
	assert "event=repl_stopped reason=user_exit" in content


def test_run_repl_handles_keyboard_interrupt(monkeypatch, capsys):
	def raise_keyboard_interrupt(_prompt):
		raise KeyboardInterrupt

	monkeypatch.setattr("builtins.input", raise_keyboard_interrupt)
	run_repl(Calculator())
	assert "Exiting calculator." in capsys.readouterr().out


def test_run_repl_handles_eof(monkeypatch, capsys):
	def raise_eof(_prompt):
		raise EOFError

	monkeypatch.setattr("builtins.input", raise_eof)
	run_repl(Calculator())
	assert "Exiting calculator." in capsys.readouterr().out


def test_run_repl_emits_success_and_info_messages(monkeypatch, capsys, tmp_path):
	calculator = Calculator(history_file=tmp_path / "history.csv", log_file=tmp_path / "events.log")
	inputs = iter(["clear", "history", "exit"])
	monkeypatch.setattr("builtins.input", lambda _prompt: next(inputs))

	run_repl(calculator)

	output = capsys.readouterr().out
	assert "History cleared." in output
	assert "History is empty." in output


def test_run_repl_emits_error_message_for_unknown_command(monkeypatch, capsys, tmp_path):
	calculator = Calculator(history_file=tmp_path / "history.csv", log_file=tmp_path / "events.log")
	inputs = iter(["foobar", "exit"])
	monkeypatch.setattr("builtins.input", lambda _prompt: next(inputs))

	run_repl(calculator)

	output = capsys.readouterr().out
	assert "Unknown command 'foobar'" in output


def test_run_repl_handles_unexpected_exception(monkeypatch, capsys):
	inputs = iter(["help", "exit"])

	def flaky_input(_prompt):
		value = next(inputs)
		if value == "help":
			raise RuntimeError("input broke")
		return value

	monkeypatch.setattr("builtins.input", flaky_input)
	run_repl(Calculator())
	assert "Error: input broke" in capsys.readouterr().out


def test_module_run_command_function_returns_exit_sentinel(tmp_path):
	from app.calculator import run_command

	calculator = Calculator(history_file=tmp_path / "history.csv")
	assert run_command(calculator, "help").startswith("Available commands")
	assert run_command(calculator, "exit") == "exit"


def test_colorize_output_variants():
	assert colorize_output("done", level="success", use_color=False) == "done"
	assert "ok" in colorize_output("ok", level="success", use_color=True)
	assert "failed" in colorize_output("failed", level="error", use_color=True)
	assert "watch out" in colorize_output("watch out", level="warning", use_color=True)
	assert "hello" in colorize_output("hello", level="other", use_color=True)
	assert "custom" in colorize_output("custom", color="red", use_color=True)


def test_colorize_output_with_mocked_colorama_palette_paths(monkeypatch):
	class _Fore:
		GREEN = "G"
		RED = "R"
		YELLOW = "Y"
		CYAN = "C"

	class _Style:
		RESET_ALL = "!"

	class _Colorama:
		Fore = _Fore
		Style = _Style

	import sys

	monkeypatch.setitem(sys.modules, "colorama", _Colorama)
	assert colorize_output("ok", level="success") == "Gok!"
	assert colorize_output("ok", color="green") == "Gok!"
	assert colorize_output("ok", color="unknown") == "Cok!"


def test_colorize_output_returns_plain_text_when_colorama_import_fails(monkeypatch):
	import builtins

	original_import = builtins.__import__

	def _import_with_colorama_error(name, *args, **kwargs):
		if name == "colorama":
			raise ImportError("simulated missing dependency")
		return original_import(name, *args, **kwargs)

	monkeypatch.setattr(builtins, "__import__", _import_with_colorama_error)
	assert colorize_output("plain", level="success", use_color=True) == "plain"


def test_repl_message_level_strategy_default_classification():
	strategy = ReplMessageLevelStrategy()
	assert strategy.classify("Exiting calculator.", should_exit=True) == "warning"
	assert strategy.classify("Error: boom", should_exit=False) == "error"
	assert strategy.classify("Unknown command 'x'", should_exit=False) == "error"
	assert strategy.classify("Undo successful.", should_exit=False) == "success"
	assert strategy.classify("History saved.", should_exit=False) == "success"
	assert strategy.classify("History is empty.", should_exit=False) == "info"


def test_run_repl_uses_custom_presentation_config(monkeypatch, capsys, tmp_path):
	calculator = Calculator(history_file=tmp_path / "history.csv", log_file=tmp_path / "events.log")
	custom_config = ReplPresentationConfig(prompt="mycalc> ", welcome_message="Welcome!", use_color=False)
	inputs = iter(["exit"])
	monkeypatch.setattr("builtins.input", lambda prompt: next(inputs))

	run_repl(calculator, presentation_config=custom_config)

	output = capsys.readouterr().out
	assert "Welcome!" in output
	assert "Exiting calculator." in output
