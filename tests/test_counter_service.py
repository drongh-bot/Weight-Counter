from app.models.biz_result import BizState
from app.models.parameter_manager import ParameterManager
from app.models.piece_counter import CounterState
from app.services.counter_service import CounterService


class TestCounterServiceProcess:
    @staticmethod
    def _make_service(target=100):
        params = ParameterManager()
        params.load()
        params.target_pieces = target
        return CounterService(params)

    def test_initial_state(self, qapp):
        svc = self._make_service()
        result = svc.current_result()
        assert result.state == BizState.ZERO
        assert result.total_pieces == 0

    def test_zero_to_normal(self, qapp):
        svc = self._make_service()
        result = svc.process(10.0)
        assert result.state == BizState.NORMAL
        assert result.total_pieces == 1

    def test_normal_add_multiple(self, qapp):
        svc = self._make_service()
        svc.process(10.0)
        svc.process(20.0)
        result = svc.process(30.0)
        assert result.state == BizState.NORMAL
        assert result.total_pieces == 3

    def test_abnormal_edge_trigger(self, qapp):
        svc = self._make_service()
        svc.process(10.0)
        svc.process(25.0)  # 无法匹配 → 异常
        assert svc.consume_abnormal_edge() is True
        assert svc.consume_abnormal_edge() is False  # 已消费

    def test_target_edge_trigger(self, qapp):
        svc = self._make_service(target=3)
        svc.process(10.0)   # 1件
        svc.process(20.0)   # 2件
        svc.process(30.0)   # 3件，达到目标
        assert svc.consume_target_edge() is True
        assert svc.consume_target_edge() is False

    def test_target_not_triggered_below_target(self, qapp):
        svc = self._make_service(target=10)
        svc.process(10.0)
        svc.process(20.0)
        assert svc.consume_target_edge() is False

    def test_target_not_triggered_in_abnormal(self, qapp):
        svc = self._make_service(target=2)
        svc.process(10.0)
        # 目标只应在 NORMAL 状态下触发
        result = svc.current_result()
        assert result.total_pieces == 1
        assert svc.consume_target_edge() is False

    def test_added_flag(self, qapp):
        svc = self._make_service()
        result = svc.process(10.0)
        assert result.added is True
        result = svc.process(10.0)  # 无变化
        assert result.added is False

    def test_force_accept(self, qapp):
        svc = self._make_service()
        svc.counter.last_stable_weight = 100.0
        svc.force_accept(100.0)
        result = svc.current_result()
        assert result.total_pieces == svc.params.force_pieces

    def test_clear_abnormal(self, qapp):
        svc = self._make_service()
        svc.process(10.0)
        svc.process(25.0)  # 进入异常
        assert svc.counter.state == CounterState.ABNORMAL
        svc.clear_abnormal(10.0)
        assert svc.counter.state == CounterState.NORMAL

    def test_reset(self, qapp):
        svc = self._make_service()
        svc.process(10.0)
        svc.process(20.0)
        assert svc.current_result().total_pieces == 2
        svc.reset()
        result = svc.current_result()
        assert result.state == BizState.ZERO
        assert result.total_pieces == 0

    def test_abnormal_result_mapping(self, qapp):
        svc = self._make_service()
        svc.process(10.0)
        result = svc.process(25.0)  # 异常
        assert result.state == BizState.ABNORMAL
        assert result.abnormal_high is True
        assert result.abnormal_low is False

    def test_current_result_snapshot(self, qapp):
        svc = self._make_service()
        svc.process(10.0)
        result = svc.current_result()
        assert result.total_pieces == 1
        assert result.avg_weight == 10.0
        assert result.weights == [10.0]
