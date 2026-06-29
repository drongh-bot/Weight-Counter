from app.models.params import Params
from app.models.counter_state import CounterState
from app.services.counter_service import CounterService


class TestCounterServiceProcess:
    @staticmethod
    def _make_service(target=100):
        params = Params()
        params.target_pieces = target
        return CounterService(params)

    def test_initial_state(self):
        svc = self._make_service()
        result = svc.current_result()
        assert result.state == CounterState.ZERO
        assert result.total_pieces == 0

    def test_zero_to_normal(self):
        svc = self._make_service()
        result = svc.process(10.0)
        assert result.state == CounterState.NORMAL
        assert result.total_pieces == 1

    def test_normal_add_multiple(self):
        svc = self._make_service()
        svc.process(10.0)
        svc.process(20.0)
        result = svc.process(30.0)
        assert result.state == CounterState.NORMAL
        assert result.total_pieces == 3

    def test_abnormal_edge_trigger(self):
        svc = self._make_service()
        svc.process(10.0)
        svc.process(25.0)  # 无法匹配 → 异常
        assert svc.consume_abnormal_edge() is True
        assert svc.consume_abnormal_edge() is False  # 已消费

    def test_target_edge_trigger(self):
        svc = self._make_service(target=3)
        svc.process(10.0)   # 1件
        svc.process(20.0)   # 2件
        svc.process(30.0)   # 3件，达到目标
        assert svc.consume_target_edge() is True
        assert svc.consume_target_edge() is False

    def test_target_not_triggered_below_target(self):
        svc = self._make_service(target=10)
        svc.process(10.0)
        svc.process(20.0)
        assert svc.consume_target_edge() is False

    def test_target_not_triggered_in_abnormal(self):
        svc = self._make_service(target=2)
        svc.process(10.0)
        # 目标只应在 NORMAL 状态下触发
        result = svc.current_result()
        assert result.total_pieces == 1
        assert svc.consume_target_edge() is False

    def test_added_flag(self):
        svc = self._make_service()
        result = svc.process(10.0)
        assert result.added is True
        result = svc.process(10.0)  # 无变化
        assert result.added is False

    def test_force_accept(self):
        svc = self._make_service()
        svc._piece_counter.last_stable_weight = 100.0
        svc.force_accept(100.0, 10)
        result = svc.current_result()
        assert result.total_pieces == 10

    def test_clear_abnormal(self):
        svc = self._make_service()
        svc.process(10.0)
        svc.process(25.0)  # 进入异常
        assert svc._piece_counter.state == CounterState.ABNORMAL
        svc.clear_abnormal(10.0)
        assert svc._piece_counter.state == CounterState.NORMAL

    def test_reset(self):
        svc = self._make_service()
        svc.process(10.0)
        svc.process(20.0)
        assert svc.current_result().total_pieces == 2
        svc.reset()
        result = svc.current_result()
        assert result.state == CounterState.ZERO
        assert result.total_pieces == 0

    def test_abnormal_result_mapping(self):
        svc = self._make_service()
        svc.process(10.0)
        result = svc.process(25.0)  # 异常
        assert result.state == CounterState.ABNORMAL
        assert result.abnormal_high is True
        assert result.abnormal_low is False

    def test_current_result_snapshot(self):
        svc = self._make_service()
        svc.process(10.0)
        result = svc.current_result()
        assert result.total_pieces == 1
        assert result.avg_weight == 10.0
        assert result.weights == [10.0]

    def test_apply_params_syncs_ui_editable_fields(self):
        params = Params(
            initial_mini_weight=0.5,
            tolerance_percent=20.0,
            stability_threshold=0.02,
            max_batch_pieces=1,
            initial_single_pieces=5,
            decimal_places=2,
        )
        svc = CounterService(params)

        params.initial_mini_weight = 1.0
        params.tolerance_percent = 15.0
        params.stability_threshold = 0.10
        params.max_batch_pieces = 2
        params.initial_single_pieces = 8
        params.decimal_places = 3

        svc.apply_params()

        pc = svc._piece_counter
        assert pc.initial_mini_weight == 1.0
        assert pc.tolerance.tolerance_percent == 15.0
        assert pc.max_batch_pieces == 2
        assert pc.initial_single_pieces == 8
        assert pc.decimal_places == 3
        assert pc.tolerance.min_tol == max(0.002, 0.20)
        assert svc.current_result().decimal_places == 3
