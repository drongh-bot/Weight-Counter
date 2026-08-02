from app.models.counter_state import CounterState
from app.presentation.status_bar import (
    MSG_ABNORMAL,
    MSG_FORCE_DONE,
    MSG_FORCE_FAIL,
    MSG_NONE,
    MSG_TARGET,
    MSG_WAIT_STABLE,
    ForceOutcome,
    StatusBar,
)
from app.presentation.styles import Styles


class TestStatusBarLink:
    def test_ok_after_reset(self):
        snap = StatusBar().reset()
        assert snap.parse.text == "解析正常"
        assert snap.comm.text == "通讯正常"

    def test_timeout_labels(self):
        snap = StatusBar().on_timeout()
        assert snap.parse.text == "解析等待"
        assert snap.comm.text == "通讯等待"

    def test_parse_fail_labels(self):
        snap = StatusBar().on_parse_fail()
        assert snap.parse.text == "解析异常"
        assert snap.comm.text == "通讯正常"


class TestStatusBarMessage:
    def test_abnormal_from_state(self):
        bar = StatusBar()
        snap = bar.on_stable_frame(
            state=CounterState.ABNORMAL,
            force=ForceOutcome.NONE,
            target_reached=False,
            piece_added=False,
        )
        assert snap.message.text == MSG_ABNORMAL
        assert snap.message.style == Styles.GRAY

    def test_target_latch_until_later_add(self):
        bar = StatusBar()
        bar.on_stable_frame(
            state=CounterState.NORMAL,
            force=ForceOutcome.NONE,
            target_reached=True,
            piece_added=True,
        )
        assert bar.snapshot().message.text == MSG_TARGET

        bar.on_stable_frame(
            state=CounterState.NORMAL,
            force=ForceOutcome.NONE,
            target_reached=False,
            piece_added=True,
        )
        assert bar.snapshot().message.text == MSG_NONE

    def test_force_overrides_then_falls_back(self):
        bar = StatusBar()
        bar.on_stable_frame(
            state=CounterState.ABNORMAL,
            force=ForceOutcome.NONE,
            target_reached=False,
            piece_added=False,
        )
        assert (
            bar.snapshot(force=ForceOutcome.FAIL).message.text == MSG_FORCE_FAIL
        )
        assert bar.snapshot(force=ForceOutcome.DONE).message.text == MSG_FORCE_DONE
        assert bar.snapshot().message.text == MSG_ABNORMAL

    def test_waiting_cleared_on_stable(self):
        bar = StatusBar()
        assert bar.on_force_waiting().message.text == MSG_WAIT_STABLE
        snap = bar.on_stable_frame(
            state=CounterState.NORMAL,
            force=ForceOutcome.NONE,
            target_reached=False,
            piece_added=False,
        )
        assert snap.message.text == MSG_NONE

    def test_error_cleared_on_stable(self):
        bar = StatusBar()
        assert bar.on_csv_error("串口错误").message.text == "串口错误"
        assert bar.on_csv_error("串口错误").message.style == Styles.RED
        snap = bar.on_stable_frame(
            state=CounterState.NORMAL,
            force=ForceOutcome.NONE,
            target_reached=False,
            piece_added=False,
        )
        assert snap.message.text == MSG_NONE

    def test_waiting_over_abnormal(self):
        bar = StatusBar()
        bar.on_stable_frame(
            state=CounterState.ABNORMAL,
            force=ForceOutcome.NONE,
            target_reached=False,
            piece_added=False,
        )
        assert bar.on_force_waiting().message.text == MSG_WAIT_STABLE


class TestStatusBarIntegration:
    def test_timeout_preserves_message(self):
        bar = StatusBar()
        bar.on_stable_frame(
            state=CounterState.ABNORMAL,
            force=ForceOutcome.NONE,
            target_reached=False,
            piece_added=False,
        )
        snap = bar.on_timeout()
        assert snap.comm.text == "通讯等待"
        assert snap.message.text == MSG_ABNORMAL

    def test_parse_fail_preserves_message(self):
        bar = StatusBar()
        bar.on_csv_error("保留")
        snap = bar.on_parse_fail()
        assert snap.parse.text == "解析异常"
        assert snap.message.text == "保留"

    def test_force_waiting_then_done_then_target(self):
        bar = StatusBar()
        assert bar.on_force_waiting().message.text == MSG_WAIT_STABLE
        snap = bar.on_stable_frame(
            state=CounterState.NORMAL,
            force=ForceOutcome.DONE,
            target_reached=True,
            piece_added=False,
        )
        assert snap.message.text == MSG_FORCE_DONE
        assert bar.on_stable_frame(
            state=CounterState.NORMAL,
            force=ForceOutcome.NONE,
            target_reached=False,
            piece_added=False,
        ).message.text == MSG_TARGET

    def test_reset(self):
        bar = StatusBar()
        bar.on_force_waiting()
        bar.on_stable_frame(
            state=CounterState.ABNORMAL,
            force=ForceOutcome.NONE,
            target_reached=True,
            piece_added=False,
        )
        snap = bar.reset()
        assert snap.message.text == MSG_NONE
        assert snap.parse.text == "解析正常"
