import pytest
from app.models.counter_state import CounterState
from app.models.piece_counter import (
    PieceCounter,
    Thresholds,
    Tolerance,
    WeightLearner,
)


class TestThresholds:
    def test_dynamic_mini_weight_normal(self):
        """avg_weight > 0 时 = max(avg * 0.5, initial * 0.3)"""
        th = Thresholds(
            initial_mini_weight=0.5,
            avg_weight=10.0,
            tolerance_percent=10.0,
            min_tol=0.04,
        )
        expected = max(10.0 * 0.5, 0.5 * 0.3)
        assert th.dynamic_mini_weight == expected

    def test_dynamic_mini_weight_zero_avg(self):
        """avg_weight = 0 时 = initial_mini_weight"""
        th = Thresholds(
            initial_mini_weight=0.5,
            avg_weight=0.0,
            tolerance_percent=10.0,
            min_tol=0.04,
        )
        assert th.dynamic_mini_weight == 0.5

    def test_recover_threshold(self):
        """恢复正常阈值 = max(avg * tolerance%, min_tol)"""
        th = Thresholds(
            initial_mini_weight=0.5,
            avg_weight=5.0,
            tolerance_percent=20.0,
            min_tol=0.1,
        )
        expected = max(5.0 * 0.20, 0.1)
        assert th.recover_threshold == expected

    def test_recover_threshold_zero_avg(self):
        """avg_weight = 0 时的恢复阈值"""
        th = Thresholds(
            initial_mini_weight=0.5,
            avg_weight=0.0,
            tolerance_percent=20.0,
            min_tol=0.1,
        )
        assert th.recover_threshold == max(0.5, 0.1)

    def test_update_changes_avg(self):
        """update 更新 avg_weight"""
        th = Thresholds(
            initial_mini_weight=0.5,
            avg_weight=3.0,
            tolerance_percent=10.0,
            min_tol=0.04,
        )
        th.update(7.0)
        assert th.avg_weight == 7.0


class TestWeightLearner:
    def test_first_piece(self):
        """第一件直接返回 piece_weight"""
        learner = WeightLearner()
        result = learner.update(avg_weight=0.0, piece_weight=10.0, n=1, total_pieces=1)
        assert result == 10.0

    def test_early_averaging(self):
        """≤5 件时使用加权平均"""
        learner = WeightLearner()
        # First piece
        avg = learner.update(0.0, 10.0, 1, 1)
        assert avg == 10.0
        # Second piece — plain average
        avg = learner.update(avg, 10.0, 1, 2)
        assert avg == 10.0
        # Third piece with different weight
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
        # Establish average
        avg = 10.0
        for _ in range(6):
            avg = learner.update(avg, 10.0, 1, 10)
        # Two consecutive jumps
        avg = learner.update(avg, 20.0, 1, 11)  # diff_ratio = 1.0 > 0.5
        assert learner.jump_count == 1
        avg = learner.update(avg, 20.0, 1, 12)
        # After confirmed jump, returns piece_weight directly
        assert avg == 20.0
        assert learner.jump_count == 0

    def test_jump_not_confirmed(self):
        """单次跳变后恢复正常，不触发"""
        learner = WeightLearner()
        avg = 10.0
        for _ in range(6):
            avg = learner.update(avg, 10.0, 1, 10)
        # Single jump
        avg = learner.update(avg, 20.0, 1, 11)
        assert learner.jump_count == 1
        # Return to normal
        avg = learner.update(avg, 10.0, 1, 12)
        assert learner.jump_count == 0

    def test_reset(self):
        learner = WeightLearner()
        learner.jump_count = 3
        learner.reset()
        assert learner.jump_count == 0


class TestTolerance:
    def test_update_sets_range(self):
        """update 设置公差范围"""
        tol = Tolerance(min_tol=0.1, tolerance_percent=10.0)
        tol.update(100.0)
        assert tol.low < 100.0
        assert tol.high > 100.0
        assert tol.half_range > 0

    def test_update_zero_avg_resets(self):
        """avg_weight = 0 时全部重置为 0"""
        tol = Tolerance(min_tol=0.1, tolerance_percent=10.0)
        tol.update(0.0)
        assert tol.low == 0
        assert tol.high == 0
        assert tol.half_range == 0

    def test_match_single_piece(self):
        """单件偏差在公差内 → True"""
        tol = Tolerance(min_tol=0.1, tolerance_percent=10.0)
        tol.update(10.0)
        # delta = 10.0 → 1 piece exactly
        assert tol.is_within_tolerance(abs(10.0), 1)

    def test_match_multi_piece(self):
        """sqrt(n) 公差模型"""
        tol = Tolerance(min_tol=0.1, tolerance_percent=10.0)
        tol.update(10.0)
        # 4 pieces = ~40.0, sqrt(4) = 2, tolerance scaled by 2
        assert tol.is_within_tolerance(40.0, 4)

    def test_match_failure(self):
        """超出公差 → False"""
        tol = Tolerance(min_tol=0.1, tolerance_percent=10.0)
        tol.update(10.0)
        # delta = 25.0 for 1 piece (expected ~10.0, far outside tolerance)
        assert not tol.is_within_tolerance(25.0, 1)

    def test_match_zero_avg(self):
        """avg_weight ≤ 0 时直接返回 False"""
        tol = Tolerance(min_tol=0.1, tolerance_percent=10.0)
        tol.update(0.0)
        assert not tol.is_within_tolerance(10.0, 1)


class TestPieceCounterFSM:
    def test_initial_state(self):
        counter = PieceCounter()
        assert counter.state == CounterState.ZERO
        assert counter.total_pieces == 0

    def test_zero_below_threshold_stays_zero(self):
        """重量 < initial_mini_weight，保持 ZERO"""
        counter = PieceCounter(initial_mini_weight=0.5)
        counter.process(0.3)
        assert counter.state == CounterState.ZERO
        assert counter.total_pieces == 0

    def test_zero_to_normal(self):
        """重量 > initial_mini_weight，ZERO → NORMAL，添加 1 件"""
        counter = PieceCounter(initial_mini_weight=0.5)
        # base weight is 0, delta = 10.0
        counter.process(10.0)
        assert counter.state == CounterState.NORMAL
        assert counter.total_pieces == 1

    def test_normal_add_pieces(self):
        """NORMAL 状态添加多件"""
        counter = PieceCounter(
            initial_mini_weight=0.5,
            tolerance_percent=10.0,
            max_batch_pieces=4,
        )
        # 建立第一件
        counter.process(10.0)
        assert counter.total_pieces == 1
        # 再加一件
        counter.process(20.0)
        assert counter.total_pieces == 2
        assert counter.state == CounterState.NORMAL

    def test_normal_to_abnormal(self):
        """增量无法匹配整数件数 → ABNORMAL"""
        counter = PieceCounter(
            initial_mini_weight=0.5,
            tolerance_percent=10.0,
            max_batch_pieces=4,
        )
        # 建立基准重量
        counter.process(10.0)
        assert counter.total_pieces == 1
        # 增量 15.0：n_est=1.5, round=2, 超出学习阶段 limit=1
        counter.process(25.0)
        assert counter.state == CounterState.ABNORMAL

    def test_abnormal_recovery(self):
        """ABNORMAL 下重量回到基准附近自动恢复"""
        counter = PieceCounter(
            initial_mini_weight=0.5,
            tolerance_percent=20.0,
            max_batch_pieces=4,
        )
        counter.process(10.0)
        assert counter.total_pieces == 1
        # 增量超过 dynamic_mini_weight 且无法匹配 → 异常
        counter.process(25.0)
        assert counter.state == CounterState.ABNORMAL
        # 回到基准附近触发恢复
        counter.process(10.0)
        assert counter.state == CounterState.NORMAL

    def test_abnormal_high_direction(self):
        """ABNORMAL 高位异常方向追踪"""
        counter = PieceCounter(
            initial_mini_weight=0.5,
            tolerance_percent=20.0,
        )
        counter.process(10.0)
        counter.process(15.0)  # 异常
        assert counter.state == CounterState.ABNORMAL
        assert counter.abnormal_high
        assert not counter.abnormal_low

    def test_abnormal_low_direction(self):
        """ABNORMAL 低位异常方向追踪（模拟减件异常）"""
        counter = PieceCounter(
            initial_mini_weight=0.5,
            tolerance_percent=20.0,
            max_batch_pieces=4,
        )
        counter.process(10.0)   # 1件
        counter.process(20.0)   # 2件
        counter.process(30.0)   # 3件
        assert counter.total_pieces == 3
        # 减到半件值 → 异常（减了多少不确定）
        counter.process(25.0)
        assert counter.state == CounterState.ABNORMAL
        assert counter.abnormal_low
        assert not counter.abnormal_high

    def test_force_accept(self):
        """强制校准，重置为指定件数"""
        counter = PieceCounter(initial_mini_weight=0.5)
        counter.force_accept(100.0, 10)
        assert counter.total_pieces == 10
        assert counter.avg_weight == pytest.approx(10.0)
        assert counter.state != CounterState.ABNORMAL

    def test_force_accept_below_threshold_ignored(self):
        """强制校准重量不足阈值，忽略"""
        counter = PieceCounter(initial_mini_weight=1.0)
        counter.process(10.0)  # 先建立一个正常状态
        counter.force_accept(0.3, 5)
        assert counter.total_pieces == 1  # 未改变

    def test_global_zero_reset(self):
        """任意状态下重量归零，全局复位"""
        counter = PieceCounter(initial_mini_weight=0.5)
        counter.process(10.0)   # NORMAL
        counter.process(15.0)   # ABNORMAL
        assert counter.state == CounterState.ABNORMAL
        # 重量归零
        counter.process(0.0)
        assert counter.state == CounterState.ZERO
        assert counter.total_pieces == 0

    def test_jitter_filter(self):
        """NORMAL 下微小波动被忽略"""
        counter = PieceCounter(
            initial_mini_weight=0.5, tolerance_percent=10.0,
        )
        counter.process(10.0)
        assert counter.total_pieces == 1
        # 微小波动（< min_tol）
        counter.process(10.01)
        assert counter.total_pieces == 1

    def test_reset(self):
        """reset 后恢复初始状态"""
        counter = PieceCounter(initial_mini_weight=0.5)
        counter.process(10.0)
        counter.process(20.0)
        assert counter.total_pieces == 2
        counter.reset()
        assert counter.state == CounterState.ZERO
        assert counter.total_pieces == 0
        assert counter.avg_weight == 0.0
        assert counter.delta == 0.0

    def test_initial_single_pieces_limit(self):
        """学习阶段（件数 < initial_single_pieces）只能逐件添加"""
        counter = PieceCounter(
            initial_mini_weight=0.5,
            initial_single_pieces=5,
        )
        counter.process(10.0)
        assert counter.total_pieces == 1
        # 尝试加大量（模拟加多件入），但处于学习阶段只能加 1
        counter.process(10.0 + 9.9)  # should only add 1
        assert counter.total_pieces == 2
