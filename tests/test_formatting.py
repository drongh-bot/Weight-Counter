from app.models.formatting import format_weight


class TestFormatWeight:
    def test_two_decimals(self):
        assert format_weight(10.0, 2) == "10.00"

    def test_zero_decimals(self):
        assert format_weight(10.5, 0) == "10"

    def test_negative_value(self):
        assert format_weight(-1.234, 3) == "-1.234"
