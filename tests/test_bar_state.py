from app.models.counter_state import CounterState
from app.presentation.bar_state import (
    MSG_ABNORMAL,
    MSG_FORCE_DONE,
    MSG_FORCE_FAIL,
    MSG_NONE,
    MSG_TARGET,
    MSG_WAIT_STABLE,
    BarState,
)
from app.presentation.view_data import Styles


class TestBarStateLink:
    def test_ok_after_reset(self):
        snap = BarState().reset()
        assert snap.parse.text == "解析正常"
        assert snap.comm.text == "通讯正常"

    def test_timeout_labels(self):
        snap = BarState().on_timeout()
        assert snap.parse.text == "解析等待"
        assert snap.comm.text == "通讯等待"

    def test_parse_fail_labels(self):
        snap = BarState().on_parse_fail()
        assert snap.parse.text == "解析异常"
        assert snap.comm.text == "通讯正常"


class TestBarStateMessage:
    def test_abnormal_from_state(self):
        bar = BarState()
        snap = bar.on_stable_frame(
            state=CounterState.ABNORMAL,
            target_edge=False,
            piece_added=False,
        )
        assert snap.message.text == MSG_ABNORMAL
        assert snap.message.style == Styles.GRAY

    def test_target_latch_until_later_add(self):
        bar = BarState()
        bar.on_stable_frame(
            state=CounterState.NORMAL,
            target_edge=True,
            piece_added=True,
        )
        assert bar.bar_snapshot().message.text == MSG_TARGET

        bar.on_stable_frame(
            state=CounterState.NORMAL,
            target_edge=False,
            piece_added=True,
        )
        assert bar.bar_snapshot().message.text == MSG_NONE

    def test_force_overrides_then_falls_back(self):
        bar = BarState()
        bar.on_stable_frame(
            state=CounterState.ABNORMAL,
            target_edge=False,
            piece_added=False,
        )
        assert (
            bar.on_force_fail_frame(
                state=CounterState.ABNORMAL,
                target_edge=False,
                piece_added=False,
            ).message.text
            == MSG_FORCE_FAIL
        )
        assert (
            bar.on_force_done_frame(
                state=CounterState.ABNORMAL,
                target_edge=False,
                piece_added=False,
            ).message.text
            == MSG_FORCE_DONE
        )
        assert bar.bar_snapshot().message.text == MSG_ABNORMAL

    def test_waiting_cleared_on_stable(self):
        bar = BarState()
        assert bar.on_force_waiting_frame().message.text == MSG_WAIT_STABLE
        snap = bar.on_stable_frame(
            state=CounterState.NORMAL,
            target_edge=False,
            piece_added=False,
        )
        assert snap.message.text == MSG_NONE

    def test_error_cleared_on_stable(self):
        bar = BarState()
        assert bar.on_csv_error("串口错误").message.text == "串口错误"
        assert bar.on_csv_error("串口错误").message.style == Styles.RED
        snap = bar.on_stable_frame(
            state=CounterState.NORMAL,
            target_edge=False,
            piece_added=False,
        )
        assert snap.message.text == MSG_NONE

    def test_waiting_over_abnormal(self):
        bar = BarState()
        bar.on_stable_frame(
            state=CounterState.ABNORMAL,
            target_edge=False,
            piece_added=False,
        )
        assert bar.on_force_waiting_frame().message.text == MSG_WAIT_STABLE


class TestBarStateIntegration:
    def test_timeout_preserves_message(self):
        bar = BarState()
        bar.on_stable_frame(
            state=CounterState.ABNORMAL,
            target_edge=False,
            piece_added=False,
        )
        snap = bar.on_timeout()
        assert snap.comm.text == "通讯等待"
        assert snap.message.text == MSG_ABNORMAL

    def test_parse_fail_preserves_message(self):
        bar = BarState()
        bar.on_csv_error("保留")
        snap = bar.on_parse_fail()
        assert snap.parse.text == "解析异常"
        assert snap.message.text == "保留"

    def test_force_waiting_then_done_then_target(self):
        bar = BarState()
        assert bar.on_force_waiting_frame().message.text == MSG_WAIT_STABLE
        snap = bar.on_force_done_frame(
            state=CounterState.NORMAL,
            target_edge=True,
            piece_added=False,
        )
        assert snap.message.text == MSG_FORCE_DONE
        assert (
            bar.on_stable_frame(
                state=CounterState.NORMAL,
                target_edge=False,
                piece_added=False,
            ).message.text
            == MSG_TARGET
        )

    def test_reset(self):
        bar = BarState()
        bar.on_force_waiting_frame()
        bar.on_stable_frame(
            state=CounterState.ABNORMAL,
            target_edge=True,
            piece_added=False,
        )
        snap = bar.reset()
        assert snap.message.text == MSG_NONE
        assert snap.parse.text == "解析正常"
