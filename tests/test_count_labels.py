from app.models.counter_state import CounterState
from app.presentation.count_labels import delta_style, state_label
from app.presentation.view_models import Styles
from tests.conftest import make_count_snapshot


class TestStateLabel:
    def test_zero(self):
        item = state_label(make_count_snapshot())
        assert item.text == "等待第一件"
        assert item.style == ""

    def test_normal(self):
        item = state_label(make_count_snapshot(state=CounterState.NORMAL))
        assert item.text == "正常"
        assert item.style == ""

    def test_abnormal_high(self):
        item = state_label(
            make_count_snapshot(
                state=CounterState.ABNORMAL,
                abnormal_high=True,
            )
        )
        assert item.text == "异常（偏高）"
        assert item.style == Styles.ABNORMAL_HIGH

    def test_abnormal_low(self):
        item = state_label(
            make_count_snapshot(
                state=CounterState.ABNORMAL,
                abnormal_low=True,
            )
        )
        assert item.text == "异常（偏低）"
        assert item.style == Styles.ABNORMAL_LOW


class TestDeltaStyle:
    def test_normal_empty(self):
        assert delta_style(make_count_snapshot(state=CounterState.NORMAL)) == ""

    def test_abnormal_matches_state(self):
        snap = make_count_snapshot(
            state=CounterState.ABNORMAL,
            abnormal_high=True,
        )
        assert delta_style(snap) == Styles.ABNORMAL_HIGH
