import pytest

from app.models.counter_state import CounterState
from app.models.params import Params
from app.models.piece_counter import PieceCounter
from app.models.thresholds import Thresholds
from app.models.tolerance import Tolerance
from app.models.weight_learner import WeightLearner


def _pc(**kwargs) -> PieceCounter:
    return PieceCounter(Params(**kwargs))


class TestThresholds:
    def test_dynamic_min_weight_normal(self):
        """avg_weight > 0 时 = max(avg * 0.5, initial * 0.3)"""
        th = Thresholds(
            initial_min_weight=0.5,
            tolerance_percent=10.0,
            min_tol=0.04,
        )
        expected = max(10.0 * 0.5, 0.5 * 0.3)
        assert th.dynamic_min_weight(10.0) == expected

    def test_dynamic_min_weight_zero_avg(self):
        """avg_weight = 0 时 = initial_min_weight"""
        th = Thresholds(
            initial_min_weight=0.5,
            tolerance_percent=10.0,
            min_tol=0.04,
        )
        assert th.dynamic_min_weight(0.0) == 0.5

    def test_recover_threshold(self):
        """恢复正常阈值 = max(avg * tolerance%, min_tol)"""
        th = Thresholds(
            initial_min_weight=0.5,
            tolerance_percent=20.0,
            min_tol=0.1,
        )
        expected = max(5.0 * 0.20, 0.1)
        assert th.recover_threshold(5.0) == expected

    def test_recover_threshold_zero_avg(self):
        """avg_weight = 0 时的恢复阈值"""
        th = Thresholds(
            initial_min_weight=0.5,
            tolerance_percent=20.0,
            min_tol=0.1,
        )
        assert th.recover_threshold(0.0) == max(0.5, 0.1)


class TestWeightLearner:
    def test_first_piece(self):
        """第一件直接返回 piece_weight"""
        learner = WeightLearner()
        result = learner.update(avg_weight=0.0, piece_weight=10.0, n=1, total_pieces=1)
        assert result == 10.0

    def test_early_averaging(self):
        """≤5 件时使用加权平均"""
        learner = WeightLearner()
        avg = learner.update(0.0, 10.0, 1, 1)
        assert avg == 10.0
        avg = learner.update(avg, 10.0, 1, 2)
        assert avg == 10.0
        avg = learner.update(avg, 20.0, 1, 3)
        assert avg == pytest.approx((10.0 * 2 + 20.0) / 3)

    def test_ema_after_learning(self):
        """>5 件后使用动态 EMA"""
        learner = WeightLearner()
        avg = 10.0
        for _ in range(6):
            avg = learner.update(avg, 10.0, 1, 7)
        assert 10.0 * 0.05 <= avg <= 10.0 * 0.30 + 10.0 * 0.70

    def test_jump_detection(self):
        """连续 2 次偏差 >50% 触发跳变重置"""
        learner = WeightLearner()
        avg = 10.0
        for _ in range(6):
            avg = learner.update(avg, 10.0, 1, 10)
        avg = learner.update(avg, 20.0, 1, 11)
        assert learner.jump_count == 1
        avg = learner.update(avg, 20.0, 1, 12)
        assert avg == 20.0
        assert learner.jump_count == 0

    def test_jump_not_confirmed(self):
        """单次跳变后恢复正常，不触发"""
        learner = WeightLearner()
        avg = 10.0
        for _ in range(6):
            avg = learner.update(avg, 10.0, 1, 10)
        avg = learner.update(avg, 20.0, 1, 11)
        assert learner.jump_count == 1
        avg = learner.update(avg, 10.0, 1, 12)
        assert learner.jump_count == 0

    def test_reset(self):
        learner = WeightLearner()
        learner.jump_count = 3
        learner.reset()
        assert learner.jump_count == 0


class TestTolerance:
    def test_band_sets_range(self):
        tol = Tolerance(min_tol=0.1, tolerance_percent=10.0)
        low, high, half_range = tol.band(100.0)
        assert low < 100.0
        assert high > 100.0
        assert half_range > 0

    def test_band_zero_avg(self):
        tol = Tolerance(min_tol=0.1, tolerance_percent=10.0)
        assert tol.band(0.0) == (0.0, 0.0, 0.0)

    def test_match_single_piece(self):
        tol = Tolerance(min_tol=0.1, tolerance_percent=10.0)
        assert tol.is_within_tolerance(abs(10.0), 1, avg_weight=10.0)

    def test_match_multi_piece(self):
        tol = Tolerance(min_tol=0.1, tolerance_percent=10.0)
        assert tol.is_within_tolerance(40.0, 4, avg_weight=10.0)

    def test_match_failure(self):
        tol = Tolerance(min_tol=0.1, tolerance_percent=10.0)
        assert not tol.is_within_tolerance(25.0, 1, avg_weight=10.0)

    def test_match_zero_avg(self):
        tol = Tolerance(min_tol=0.1, tolerance_percent=10.0)
        assert not tol.is_within_tolerance(10.0, 1, avg_weight=0.0)


class TestPieceCounterFSM:
    def test_initial_state(self):
        counter = PieceCounter()
        assert counter.state == CounterState.ZERO
        assert counter.total_pieces == 0

    def test_zero_below_threshold_stays_zero(self):
        counter = _pc(initial_min_weight=0.5)
        counter.on_stable_weight(0.3)
        assert counter.state == CounterState.ZERO
        assert counter.total_pieces == 0

    def test_zero_to_normal(self):
        counter = _pc(initial_min_weight=0.5)
        counter.on_stable_weight(10.0)
        assert counter.state == CounterState.NORMAL
        assert counter.total_pieces == 1

    def test_normal_add_pieces(self):
        counter = _pc(
            initial_min_weight=0.5,
            tolerance_percent=10.0,
            max_batch_pieces=4,
        )
        counter.on_stable_weight(10.0)
        assert counter.total_pieces == 1
        counter.on_stable_weight(20.0)
        assert counter.total_pieces == 2
        assert counter.state == CounterState.NORMAL

    def test_normal_to_abnormal(self):
        counter = _pc(
            initial_min_weight=0.5,
            tolerance_percent=10.0,
            max_batch_pieces=4,
        )
        counter.on_stable_weight(10.0)
        assert counter.total_pieces == 1
        counter.on_stable_weight(25.0)
        assert counter.state == CounterState.ABNORMAL

    def test_abnormal_recovery(self):
        counter = _pc(
            initial_min_weight=0.5,
            tolerance_percent=20.0,
            max_batch_pieces=4,
        )
        counter.on_stable_weight(10.0)
        assert counter.total_pieces == 1
        counter.on_stable_weight(25.0)
        assert counter.state == CounterState.ABNORMAL
        counter.on_stable_weight(10.0)
        assert counter.state == CounterState.NORMAL

    def test_abnormal_high_direction(self):
        counter = _pc(
            initial_min_weight=0.5,
            tolerance_percent=20.0,
        )
        counter.on_stable_weight(10.0)
        counter.on_stable_weight(15.0)
        assert counter.state == CounterState.ABNORMAL
        assert counter.abnormal_high
        assert not counter.abnormal_low

    def test_abnormal_low_direction(self):
        counter = _pc(
            initial_min_weight=0.5,
            tolerance_percent=20.0,
            max_batch_pieces=4,
        )
        counter.on_stable_weight(10.0)
        counter.on_stable_weight(20.0)
        counter.on_stable_weight(30.0)
        assert counter.total_pieces == 3
        counter.on_stable_weight(25.0)
        assert counter.state == CounterState.ABNORMAL
        assert counter.abnormal_low
        assert not counter.abnormal_high

    def test_force_calibrate(self):
        counter = _pc(initial_min_weight=0.5)
        counter.force_calibrate(100.0, 10)
        assert counter.total_pieces == 10
        assert counter.avg_weight == pytest.approx(10.0)
        assert counter.state == CounterState.NORMAL
        assert counter.baseline_weight == pytest.approx(100.0)
        assert counter.last_stable_weight == pytest.approx(100.0)
        counter.on_stable_weight(100.0)
        assert counter.total_pieces == 10

    def test_force_calibrate_from_zero_resets_baseline(self):
        counter = _pc(initial_min_weight=0.5)
        counter.force_calibrate(100.0, 10)
        assert counter.state == CounterState.NORMAL
        assert counter.baseline_weight == pytest.approx(100.0)
        counter.on_stable_weight(100.0)
        assert counter.total_pieces == 10

    def test_force_calibrate_from_normal_resets_baseline(self):
        counter = _pc(initial_min_weight=0.5)
        counter.on_stable_weight(10.0)
        assert counter.total_pieces == 1
        counter.force_calibrate(30.0, 3)
        assert counter.total_pieces == 3
        assert counter.baseline_weight == pytest.approx(30.0)
        counter.on_stable_weight(30.0)
        assert counter.total_pieces == 3

    def test_force_calibrate_below_threshold_ignored(self):
        counter = _pc(initial_min_weight=1.0)
        counter.on_stable_weight(10.0)
        counter.force_calibrate(0.3, 5)
        assert counter.total_pieces == 1

    def test_global_zero_reset(self):
        counter = _pc(initial_min_weight=0.5)
        counter.on_stable_weight(10.0)
        counter.on_stable_weight(15.0)
        assert counter.state == CounterState.ABNORMAL
        counter.on_stable_weight(0.0)
        assert counter.state == CounterState.ZERO
        assert counter.total_pieces == 0

    def test_jitter_filter(self):
        counter = _pc(
            initial_min_weight=0.5,
            tolerance_percent=10.0,
        )
        counter.on_stable_weight(10.0)
        assert counter.total_pieces == 1
        counter.on_stable_weight(10.01)
        assert counter.total_pieces == 1

    def test_reset(self):
        counter = _pc(initial_min_weight=0.5)
        counter.on_stable_weight(10.0)
        counter.on_stable_weight(20.0)
        assert counter.total_pieces == 2
        counter.reset()
        assert counter.state == CounterState.ZERO
        assert counter.total_pieces == 0
        assert counter.avg_weight == 0.0
        assert counter.delta == 0.0

    def test_initial_single_pieces_limit(self):
        counter = _pc(
            initial_min_weight=0.5,
            initial_single_pieces=5,
        )
        counter.on_stable_weight(10.0)
        assert counter.total_pieces == 1
        counter.on_stable_weight(10.0 + 9.9)
        assert counter.total_pieces == 2


class TestPieceCounterParamUpdate:
    def test_apply_start_params_updates_min_weight(self):
        counter = _pc(initial_min_weight=0.5)
        counter.apply_start_params(Params(initial_min_weight=1.0))
        assert counter.thresholds.initial_min_weight == 1.0

    def test_apply_start_params_recalcs_min_tol_decimal(self):
        counter = _pc(decimal_places=2, stability_threshold=0.02)
        counter.apply_start_params(Params(decimal_places=3, stability_threshold=0.02))
        assert counter.decimal_places == 3
        assert counter.tolerance.min_tol == max(0.002, 0.04)

    def test_apply_start_params_recalcs_min_tol_stability(self):
        counter = _pc(decimal_places=2, stability_threshold=0.02)
        counter.apply_start_params(Params(decimal_places=2, stability_threshold=0.10))
        assert counter.tolerance.min_tol == max(0.02, 0.20)
        assert counter.thresholds.min_tol == counter.tolerance.min_tol

    def test_mid_run_params_mutation_does_not_affect_copy(self):
        """共享 Params 的中途修改在 apply_start_params 前不得泄漏进计件器。"""
        params = Params(tolerance_percent=20.0)
        counter = PieceCounter(params)
        params.tolerance_percent = 5.0
        assert counter.tolerance.tolerance_percent == 20.0
        counter.apply_start_params(params)
        assert counter.tolerance.tolerance_percent == 5.0
