from datetime import datetime, timezone

from app.calculation import Calculation


def test_calculation_to_dict_and_from_dict_round_trip():
	original = Calculation(
		operation="multiply",
		operand_1=4,
		operand_2=5,
		result=20,
		timestamp=datetime(2026, 3, 6, tzinfo=timezone.utc),
	)
	payload = original.to_dict()
	restored = Calculation.from_dict(payload)
	assert restored == original
