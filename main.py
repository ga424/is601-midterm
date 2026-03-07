from app.calculator import run_repl
from app.calculator import Calculator
from app.calculator_config import CalculatorConfig


def main() -> None:
	config = CalculatorConfig.load()
	calculator = Calculator(
		history_file=config.history_file,
		max_history_size=config.max_history_size,
		log_file=config.log_file,
		auto_save=config.auto_save,
		precision=config.precision,
		max_input_value=config.max_input_value,
		default_encoding=config.default_encoding,
	)
	run_repl(calculator)


if __name__ == "__main__":
	main()
