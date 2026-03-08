from app.calculator import run_repl
from app.calculator import Calculator, ReplPresentationConfig
from app.calculator_config import CalculatorConfig


def main() -> None:
	config = CalculatorConfig.load()
	calculator = Calculator(
		history_file=config.history_file,
		max_history_size=config.max_history_size,
		log_file=config.log_file,
		log_level=config.log_level,
		auto_save=config.auto_save,
		precision=config.precision,
		max_input_value=config.max_input_value,
		default_encoding=config.default_encoding,
	)
	repl_presentation = ReplPresentationConfig(
		prompt=config.repl_prompt,
		welcome_message=config.repl_welcome_message,
		use_color=config.repl_use_color,
	)
	run_repl(calculator, presentation_config=repl_presentation)


if __name__ == "__main__":
	main()
