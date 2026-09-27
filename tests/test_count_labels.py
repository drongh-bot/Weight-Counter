from app.models.counter_state import CounterState
from app.presentation.count_labels import build_count_display
from app.presentation.view_models import Styles
from tests.conftest import make_count_snapshot


class TestBuildCountDisplay:
    def test_formats_all_texts(self):
        snap = make_count_snapshot(
            state=CounterState.NORMAL,
            delta_weight=1.5,
            avg_weight=10.25,
            tolerance_high=12.3,
            tolerance_low=8.2,
            total_pieces=7,
            last_stable_weight=102.5,
            baseline_weight=101.0,
        )
        d = build_count_display(snap)
        assert d.delta.text == "1.50"
        assert d.delta.style == ""
        assert d.state.text == "正常"
        assert d.state.style == ""
        assert d.avg_text == "10.25"
        assert d.tol_high_text == "12.30"
        assert d.tol_low_text == "8.20"
        assert d.total_text == "7"
        assert d.last_stable_text == "102.50"
        assert d.baseline_text == "101.00"

    def test_zero_decimal_places(self):
        d = build_count_display(
            make_count_snapshot(
                decimal_places=0,
                delta_weight=-2.6,
                avg_weight=10.0,
            )
        )
        assert d.delta.text == "-3"
        assert d.avg_text == "10"

    def test_abnormal_high(self):
        d = build_count_display(
            make_count_snapshot(
                state=CounterState.ABNORMAL,
                abnormal_high=True,
            )
        )
        assert d.state.style == Styles.ABNORMAL_HIGH
        assert d.delta.style == Styles.ABNORMAL_HIGH
        assert d.state.text == "异常（偏高）"

    def test_abnormal_low(self):
        d = build_count_display(
            make_count_snapshot(
                state=CounterState.ABNORMAL,
                abnormal_low=True,
            )
        )
        assert d.state.style == Styles.ABNORMAL_LOW
        assert d.delta.style == Styles.ABNORMAL_LOW
        assert d.state.text == "异常（偏低）"

    def test_zero_state_defaults(self):
        d = build_count_display(make_count_snapshot())
        assert d.state.text == "等待第一件"
        assert d.state.style == ""
        assert d.delta.style == ""
        assert d.total_text == "0"
