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

    def test_target_edge_batch_skip(self):
        """批量加件跳过精确目标值时仍应触发（上升沿）"""
        params = Params()
        params.target_pieces = 100
        params.max_batch_pieces = 5
        params.initial_single_pieces = 1
        svc = CounterService(params)
        svc.apply_params()

        pc = svc._piece_counter
        pc.piece_weights = [10.0] * 98
        pc.avg_weight = 10.0
        pc.baseline_weight = 980.0
        pc.last_stable_weight = 980.0
        pc.state = CounterState.NORMAL
        pc._sync_all()

        svc.process(1010.0)  # 98 + 3 = 101，跳过 100
        assert svc.current_result().total_pieces == 101
        assert svc.consume_target_edge() is True

    def test_target_edge_not_repeated_when_already_above(self):
        """已在目标之上继续加件，不应重复触发"""
        params = Params()
        params.target_pieces = 100
        params.max_batch_pieces = 5
        params.initial_single_pieces = 1
        svc = CounterService(params)
        svc.apply_params()

        pc = svc._piece_counter
        pc.piece_weights = [10.0] * 100
        pc.avg_weight = 10.0
        pc.baseline_weight = 1000.0
        pc.last_stable_weight = 1000.0
        pc.state = CounterState.NORMAL
        pc._sync_all()

        svc.process(1030.0)  # 100 + 3 = 103
        assert svc.current_result().total_pieces == 103
        assert svc.consume_target_edge() is False

    def test_target_edge_retrigger_after_drop_below(self):
        """减至目标以下再加回，应再次触发"""
        params = Params()
        params.target_pieces = 3
        params.max_batch_pieces = 4
        params.tolerance_percent = 25.0
        svc = CounterService(params)
        svc.apply_params()

        svc.process(10.0)
        svc.process(20.0)
        svc.process(30.0)
        assert svc.consume_target_edge() is True

        svc.process(20.0)  # 减 1 件 → 2
        assert svc.current_result().total_pieces == 2
        assert svc.consume_target_edge() is False

        svc.process(30.0)  # 加 1 件 → 3
        assert svc.current_result().total_pieces == 3
        assert svc.consume_target_edge() is True

    def test_added_flag(self):
        svc = self._make_service()
        result = svc.process(10.0)
        assert result.added is True
        result = svc.process(10.0)  # 无变化
        assert result.added is False

    def test_force_calibrate(self):
        svc = self._make_service()
        svc._piece_counter.last_stable_weight = 100.0
        assert svc.force_calibrate(100.0, 10) is True
        result = svc.current_result()
        assert result.total_pieces == 10

    def test_force_calibrate_returns_false_when_invalid(self):
        svc = self._make_service()
        svc.process(10.0)
        assert svc.force_calibrate(0.3, 5) is False
        assert svc.current_result().total_pieces == 1

    def test_force_calibrate_target_edge(self):
        svc = self._make_service(target=3)
        svc.process(10.0)
        assert svc.force_calibrate(30.0, 3) is True
        assert svc.consume_target_edge() is True
        assert svc.process(30.0).total_pieces == 3
        assert svc.consume_target_edge() is False

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
        assert result.piece_weights == [10.0]

    def test_apply_params_syncs_ui_editable_fields(self):
        params = Params(
            initial_min_weight=0.5,
            tolerance_percent=20.0,
            stability_threshold=0.02,
            max_batch_pieces=1,
            initial_single_pieces=5,
            decimal_places=2,
        )
        svc = CounterService(params)

        params.initial_min_weight = 1.0
        params.tolerance_percent = 15.0
        params.stability_threshold = 0.10
        params.max_batch_pieces = 2
        params.initial_single_pieces = 8
        params.decimal_places = 3

        svc.apply_params()

        pc = svc._piece_counter
        assert pc.initial_min_weight == 1.0
        assert pc.tolerance.tolerance_percent == 15.0
        assert pc.max_batch_pieces == 2
        assert pc.initial_single_pieces == 8
        assert pc.decimal_places == 3
        assert pc.tolerance.min_tol == max(0.002, 0.20)
        assert svc.current_result().decimal_places == 3
