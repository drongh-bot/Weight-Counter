from app.models.count_result import CountResult
from app.models.counter_state import CounterState
from app.presentation.count_builder import to_count_snapshot
from app.presentation.styles import Styles


class TestToCountSnapshot:
    def test_zero_state(self):
        result = CountResult(
            added=False,
            abnormal_high=False,
            abnormal_low=False,
            state=CounterState.ZERO,
            delta=0.0,
            avg_weight=0.0,
            tolerance_high=0.0,
            tolerance_low=0.0,
            total_pieces=0,
            last_stable_weight=0.0,
            baseline_weight=0.0,
            piece_weights=[],
        )
        data = to_count_snapshot(result)
        assert data.state.text == "等待第一件"
        assert data.state.style == ""
        assert data.total_pieces == "0"

    def test_normal_state(self):
        result = CountResult(
            added=True,
            abnormal_high=False,
            abnormal_low=False,
            state=CounterState.NORMAL,
            delta=10.0,
            avg_weight=10.0,
            tolerance_high=11.0,
            tolerance_low=9.0,
            total_pieces=1,
            last_stable_weight=10.0,
            baseline_weight=0.0,
            piece_weights=[10.0],
        )
        data = to_count_snapshot(result)
        assert data.state.text == "正常"
        assert data.state.style == ""
        assert data.delta_weight.text == "10.00"

    def test_abnormal_high(self):
        result = CountResult(
            added=False,
            abnormal_high=True,
            abnormal_low=False,
            state=CounterState.ABNORMAL,
            delta=15.0,
            avg_weight=10.0,
            tolerance_high=11.0,
            tolerance_low=9.0,
            total_pieces=1,
            last_stable_weight=25.0,
            baseline_weight=10.0,
            piece_weights=[10.0],
        )
        data = to_count_snapshot(result)
        assert data.state.text == "异常（偏高）"
        assert data.state.style == Styles.ABNORMAL_HIGH
        assert data.delta_weight.style == Styles.ABNORMAL_HIGH

    def test_abnormal_low(self):
        result = CountResult(
            added=False,
            abnormal_high=False,
            abnormal_low=True,
            state=CounterState.ABNORMAL,
            delta=-5.0,
            avg_weight=10.0,
            tolerance_high=11.0,
            tolerance_low=9.0,
            total_pieces=1,
            last_stable_weight=5.0,
            baseline_weight=10.0,
            piece_weights=[10.0],
        )
        data = to_count_snapshot(result)
        assert data.state.text == "异常（偏低）"
        assert data.state.style == Styles.ABNORMAL_LOW

    def test_decimal_places(self):
        result = CountResult(
            added=False,
            abnormal_high=False,
            abnormal_low=False,
            state=CounterState.NORMAL,
            delta=1.2345,
            avg_weight=1.2345,
            tolerance_high=1.5,
            tolerance_low=1.0,
            total_pieces=1,
            last_stable_weight=1.2345,
            baseline_weight=0.0,
            piece_weights=[1.2345],
            decimal_places=3,
        )
        data = to_count_snapshot(result)
        assert data.delta_weight.text == "1.234"
        assert data.avg_weight == "1.234"
