from app.models.params import Params, params_from
from app.services.weight_input_service import WeightInputService


class TestWeightInputServiceParse:
    def test_simple_float(self):
        svc = self._make_service()
        assert svc.parse("10.5") == 10.5

    def test_with_kg_suffix(self):
        svc = self._make_service()
        assert svc.parse("  10.5 KG ") == 10.5

    def test_with_g_suffix(self):
        svc = self._make_service()
        assert svc.parse("500 G") == 500.0

    def test_with_n_suffix(self):
        svc = self._make_service()
        assert svc.parse("123.45 N") == 123.45

    def test_with_nt_suffix(self):
        svc = self._make_service()
        assert svc.parse("99.9 NT") == 99.9

    def test_with_comma_split_takes_last(self):
        svc = self._make_service()
        # Simulates multi-field serial data: "ST,GS,10.5 kg"
        assert svc.parse("ST,GS,10.5") == 10.5

    def test_with_comma_and_kg(self):
        svc = self._make_service()
        assert svc.parse("ST,GS,10.5 kg") == 10.5

    def test_negative_weight(self):
        svc = self._make_service()
        assert svc.parse("-0.50") == -0.5

    def test_no_digits_returns_none(self):
        svc = self._make_service()
        assert svc.parse("ST,GS,") is None

    def test_empty_string_returns_none(self):
        svc = self._make_service()
        assert svc.parse("") is None

    def test_non_numeric_returns_none(self):
        svc = self._make_service()
        assert svc.parse("abc") is None

    def test_spaces_only_returns_none(self):
        svc = self._make_service()
        assert svc.parse("   ") is None

    def test_uppercase_normalization(self):
        svc = self._make_service()
        assert svc.parse("10.5 kg") == 10.5

    def test_unit_embedded_in_middle_not_stripped(self):
        svc = self._make_service()
        # 数字中间的 N 不再被剥掉导致静默污染，应整体判为非法
        assert svc.parse("12N34") is None

    def test_status_prefix_with_unit(self):
        svc = self._make_service()
        assert svc.parse("ST, +123.4 kg") == 123.4

    def test_space_separated_status_prefix(self):
        svc = self._make_service()
        assert svc.parse("ST +1.234 kg") == 1.234

    def test_padded_sign_after_comma(self):
        svc = self._make_service()
        assert svc.parse("ST,GS,+  1.234 kg") == 1.234
        assert svc.parse("ST,GS,-  1.234 kg") == -1.234

    def test_unit_only_returns_none(self):
        svc = self._make_service()
        assert svc.parse("G") is None
        assert svc.parse("KG") is None

    def test_leading_sign_with_unit(self):
        svc = self._make_service()
        assert svc.parse("-5.5 G") == -5.5

    def test_apply_start_params_syncs_stability_threshold(self):
        params = params_from(stability_threshold=0.02)
        svc = WeightInputService(params)

        params.start.stability_threshold = 0.10
        svc.apply_start_params()

        assert svc.stability_threshold == 0.10

    @staticmethod
    def _make_service() -> WeightInputService:
        params = Params()
        return WeightInputService(params)
