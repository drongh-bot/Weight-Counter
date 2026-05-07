from app.models.params import Params
from app.services.checker_service import CheckerService


class TestCheckerServiceParse:
    def test_simple_float(self, qapp):
        svc = self._make_service()
        assert svc.parse("10.5") == 10.5

    def test_with_kg_suffix(self, qapp):
        svc = self._make_service()
        assert svc.parse("  10.5 KG ") == 10.5

    def test_with_g_suffix(self, qapp):
        svc = self._make_service()
        assert svc.parse("500 G") == 500.0

    def test_with_n_suffix(self, qapp):
        svc = self._make_service()
        assert svc.parse("123.45 N") == 123.45

    def test_with_nt_suffix(self, qapp):
        svc = self._make_service()
        assert svc.parse("99.9 NT") == 99.9

    def test_with_comma_split_takes_last(self, qapp):
        svc = self._make_service()
        # Simulates multi-field serial data: "ST,GS,10.5 kg"
        assert svc.parse("ST,GS,10.5") == 10.5

    def test_with_comma_and_kg(self, qapp):
        svc = self._make_service()
        assert svc.parse("ST,GS,10.5 kg") == 10.5

    def test_negative_weight(self, qapp):
        svc = self._make_service()
        assert svc.parse("-0.50") == -0.5

    def test_no_digits_returns_none(self, qapp):
        svc = self._make_service()
        assert svc.parse("ST,GS,") is None

    def test_empty_string_returns_none(self, qapp):
        svc = self._make_service()
        assert svc.parse("") is None

    def test_non_numeric_returns_none(self, qapp):
        svc = self._make_service()
        assert svc.parse("abc") is None

    def test_spaces_only_returns_none(self, qapp):
        svc = self._make_service()
        assert svc.parse("   ") is None

    def test_uppercase_normalization(self, qapp):
        svc = self._make_service()
        assert svc.parse("10.5 kg") == 10.5

    @staticmethod
    def _make_service() -> CheckerService:
        params = Params()
        return CheckerService(params)
