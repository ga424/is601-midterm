from app.calculator import colorize_output


def test_colorize_output_returns_plain_text_when_color_disabled():
	message = colorize_output("done", level="success", use_color=False)
	assert message == "done"


def test_colorize_output_success_level_includes_message():
	message = colorize_output("ok", level="success", use_color=True)
	assert "ok" in message


def test_colorize_output_error_level_includes_message():
	message = colorize_output("failed", level="error", use_color=True)
	assert "failed" in message


def test_colorize_output_warning_level_includes_message():
	message = colorize_output("watch out", level="warning", use_color=True)
	assert "watch out" in message


def test_colorize_output_unknown_level_falls_back_to_info_color():
	message = colorize_output("hello", level="other", use_color=True)
	assert "hello" in message
