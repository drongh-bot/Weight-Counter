from app.models.counter_state import CounterState
from app.presentation.count_builder import to_count_snapshot
from app.presentation.styles import Styles
from tests.conftest import make_count_result


class TestToCountSnapshot:
    def test_zero_state(self):
        data = to_count_snapshot(make_count_result())
        assert data.state.text == "等待第一件"
        assert data.state.style == ""
        assert data.total_pieces == "0"

    def test_normal_state(self):
        data = to_count_snapshot(
            make_count_result(
                added=True,
                state=CounterState.NORMAL,
                delta=10.0,
                avg_weight=10.0,
                tolerance_high=11.0,
                tolerance_low=9.0,
                total_pieces=1,
                last_stable_weight=10.0,
                piece_weights=[10.0],
            )
        )
        assert data.state.text == "正常"
        assert data.state.style == ""
        assert data.delta_weight.text == "10.00"

    def test_abnormal_high(self):
        data = to_count_snapshot(
            make_count_result(
                abnormal_high=True,
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
        )
        assert data.state.text == "异常（偏高）"
        assert data.state.style == Styles.ABNORMAL_HIGH
        assert data.delta_weight.style == Styles.ABNORMAL_HIGH

    def test_abnormal_low(self):
        data = to_count_snapshot(
            make_count_result(
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
        )
        assert data.state.text == "异常（偏低）"
        assert data.state.style == Styles.ABNORMAL_LOW

    def test_decimal_places(self):
        data = to_count_snapshot(
            make_count_result(
                state=CounterState.NORMAL,
                delta=1.2345,
                avg_weight=1.2345,
                tolerance_high=1.5,
                tolerance_low=1.0,
                total_pieces=1,
                last_stable_weight=1.2345,
                piece_weights=[1.2345],
                decimal_places=3,
            )
        )
        assert data.delta_weight.text == "1.234"
        assert data.avg_weight == "1.234"
