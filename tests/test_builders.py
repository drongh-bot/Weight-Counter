from app.models.count_result import CountResult
from app.models.counter_state import CounterState
from app.services.ui.builders import CountBuilder, BarStatusBuilder
from app.services.ui.styles import Styles


class TestCountBuilder:
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
        data = CountBuilder.build(result)
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
            total_pieces=5,
            last_stable_weight=50.0,
            baseline_weight=40.0,
            piece_weights=[10.0, 10.0, 10.0, 10.0, 10.0],
        )
        data = CountBuilder.build(result)
        assert data.state.text == "正常"
        assert data.state.style == ""
        assert data.delta_weight.text == "10.00"
        assert data.delta_weight.style == ""  # NORMAL should not highlight delta
        assert data.total_pieces == "5"
        assert data.avg_weight == "10.00"

    def test_abnormal_high_state(self):
        result = CountResult(
            added=False,
            abnormal_high=True,
            abnormal_low=False,
            state=CounterState.ABNORMAL,
            delta=15.0,
            avg_weight=10.0,
            tolerance_high=11.0,
            tolerance_low=9.0,
            total_pieces=3,
            last_stable_weight=45.0,
            baseline_weight=30.0,
            piece_weights=[10.0, 10.0, 10.0],
        )
        data = CountBuilder.build(result)
        assert data.state.text == "异常（偏高）"
        assert data.state.style == Styles.ABNORMAL_HIGH
        assert data.delta_weight.style == Styles.ABNORMAL_HIGH

    def test_abnormal_low_state(self):
        result = CountResult(
            added=False,
            abnormal_high=False,
            abnormal_low=True,
            state=CounterState.ABNORMAL,
            delta=-5.0,
            avg_weight=10.0,
            tolerance_high=11.0,
            tolerance_low=9.0,
            total_pieces=2,
            last_stable_weight=15.0,
            baseline_weight=20.0,
            piece_weights=[10.0, 10.0],
        )
        data = CountBuilder.build(result)
        assert data.state.text == "异常（偏低）"
        assert data.state.style == Styles.ABNORMAL_LOW
        assert data.delta_weight.style == Styles.ABNORMAL_LOW

    def test_delta_formatting(self):
        result = CountResult(
            added=False,
            abnormal_high=False,
            abnormal_low=False,
            state=CounterState.NORMAL,
            delta=3.14159,
            avg_weight=10.0,
            tolerance_high=11.0,
            tolerance_low=9.0,
            total_pieces=1,
            last_stable_weight=10.0,
            baseline_weight=0.0,
            piece_weights=[10.0],
        )
        data = CountBuilder.build(result)
        assert data.delta_weight.text == "3.14"
        assert data.tolerance_high == "11.00"
        assert data.tolerance_low == "9.00"
        assert data.last_stable_weight == "10.00"
        assert data.baseline_weight == "0.00"


class TestBarStatusBuilder:
    def test_parse_ok_comm_ok(self):
        status = BarStatusBuilder.build(parse_ok=True, comm_ok=True, status_message="")
        assert status.parse.text == "解析正常"
        assert status.parse.style == Styles.GREEN
        assert status.comm.text == "通讯正常"
        assert status.comm.style == Styles.GREEN
        assert status.message.text == "无异常"
        assert status.message.style == ""

    def test_parse_fail_comm_fail(self):
        status = BarStatusBuilder.build(parse_ok=False, comm_ok=False, status_message=None)
        assert status.parse.text == "解析等待"
        assert status.parse.style == Styles.GRAY
        assert status.comm.text == "通讯等待"
        assert status.comm.style == Styles.GRAY
        assert status.message.text == "无异常"
        assert status.message.style == ""

    def test_parse_fail_comm_ok(self):
        status = BarStatusBuilder.build(parse_ok=False, comm_ok=True, status_message="")
        assert status.parse.text == "解析异常"
        assert status.parse.style == Styles.RED
        assert status.comm.text == "通讯正常"
        assert status.comm.style == Styles.GREEN

    def test_exception_display(self):
        status = BarStatusBuilder.build(
            parse_ok=True, comm_ok=True, status_message="串口打开失败"
        )
        assert status.message.text == "串口打开失败"
        assert status.message.style == Styles.RED

    def test_info_exception_uses_gray(self):
        status = BarStatusBuilder.build(
            parse_ok=True,
            comm_ok=True,
            status_message="等待稳定重量…",
            info=True,
        )
        assert status.message.text == "等待稳定重量…"
        assert status.message.style == Styles.GRAY
