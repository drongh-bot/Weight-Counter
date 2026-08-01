from app.models.weight_stability_checker import WeightStabilityChecker


class TestStableDetection:
    def test_stable_after_consecutive_frames(self):
        """连续 stable_count 帧稳定后返回稳定值"""
        checker = WeightStabilityChecker(
            short_win=4,
            long_win=8,
            stable_count=3,
            stability_threshold=0.02,
        )
        value = 100.0
        # 前 7 帧填充长窗口，返回 None
        for _ in range(checker.long_win.maxlen - 1):
            result = checker.check_stability(value)
            assert result is None
        # 连续 3 帧稳定后进入锁定
        for i in range(checker.stable_count_required):
            result = checker.check_stability(value)
            if i < checker.stable_count_required - 1:
                assert result is None
            else:
                assert result is not None

    def test_unstable_by_speed(self):
        """短窗口内快速变化 → 不稳定"""
        checker = WeightStabilityChecker(
            short_win=4,
            long_win=8,
            stable_count=3,
            stability_threshold=0.02,
        )
        # 先填充窗口
        for _ in range(8):
            checker.check_stability(100.0)
        # 突变超过 speed_limit
        result = checker.check_stability(110.0)
        assert result is None

    def test_unstable_by_trend(self):
        """长窗口内持续漂移 → 不稳定"""
        checker = WeightStabilityChecker(
            short_win=4,
            long_win=8,
            stable_count=3,
            stability_threshold=0.02,
        )
        # 逐步上升
        for i in range(8):
            checker.check_stability(100.0 + i * 0.5)
        # 漂移超过 trend_limit
        result = checker.check_stability(105.0)
        assert result is None

    def test_unstable_by_stddev(self):
        """长窗口内方差过大 → 不稳定"""
        checker = WeightStabilityChecker(
            short_win=4,
            long_win=8,
            stable_count=3,
            stability_threshold=0.02,
        )
        values = [100.0, 100.5, 99.5, 101.0, 98.0, 102.0, 100.0, 101.5]
        for v in values:
            checker.check_stability(v)
        result = checker.check_stability(97.0)
        assert result is None


class TestLockAndUnlock:
    def test_lock_after_stable(self):
        """稳定后锁定，持续返回稳定值"""
        checker = WeightStabilityChecker(
            short_win=4,
            long_win=8,
            stable_count=3,
            stability_threshold=0.02,
            unlock_factor=2.5,
        )
        value = 50.0
        for _ in range(10):
            checker.check_stability(value)
        # 锁定后无论继续喂相同值都返回稳定值
        for _ in range(5):
            result = checker.check_stability(value)
            assert result is not None

    def test_unlock_after_exceeding_threshold(self):
        """超过解锁阈值，连续 unlock_confirm 帧后解锁"""
        checker = WeightStabilityChecker(
            short_win=4,
            long_win=8,
            stable_count=3,
            unlock_confirm=2,
            unlock_factor=2.5,
            stability_threshold=0.02,
        )
        value = 50.0
        for _ in range(10):
            checker.check_stability(value)
        # 锁定中
        assert checker.locked
        # 突变超过锁定值 + unlock_factor * stability_threshold
        jump = 50.0 + 2.5 * 0.02 + 0.01
        # 第一帧仍锁定
        result = checker.check_stability(jump)
        assert checker.locked
        assert result is not None
        # 第二帧解锁
        result = checker.check_stability(jump)
        assert not checker.locked

    def test_no_unlock_on_minor_change(self):
        """小幅波动不足解锁阈值，保持锁定"""
        checker = WeightStabilityChecker(
            short_win=4,
            long_win=8,
            stable_count=3,
            unlock_factor=2.5,
            stability_threshold=0.02,
        )
        value = 50.0
        for _ in range(10):
            checker.check_stability(value)
        # 小幅变化，不应解锁
        for _ in range(5):
            result = checker.check_stability(value + 0.01)
            assert checker.locked
            assert result is not None


class TestEdgeCases:
    def test_early_frame_skip(self):
        """长窗口未满时不判定稳定"""
        checker = WeightStabilityChecker(
            short_win=4,
            long_win=8,
            stable_count=3,
        )
        for _ in range(5):
            result = checker.check_stability(10.0)
            assert result is None

    def test_reset(self):
        """reset 清空所有状态"""
        checker = WeightStabilityChecker(short_win=4, long_win=8)
        for _ in range(15):
            checker.check_stability(42.0)
        assert checker.locked
        checker.reset()
        assert not checker.locked
        assert checker.locked_weight is None
        assert len(checker.short_win) == 0
        assert len(checker.long_win) == 0
        assert checker.stable_counter == 0
        assert checker.last_stable_weight is None

    def test_hot_update_threshold(self):
        """set_stability_threshold 立即生效"""
        checker = WeightStabilityChecker(
            stability_threshold=10.0,
        )
        checker.set_stability_threshold(0.001)
        assert checker.stability_threshold == 0.001

    def test_hot_update_stable_count(self):
        """set_stable_count 立即生效"""
        checker = WeightStabilityChecker(stable_count=3)
        checker.set_stable_count(5)
        assert checker.stable_count_required == 5

    def test_lock_keeps_updating_windows(self):
        """锁定期间窗口持续滚动更新"""
        checker = WeightStabilityChecker(
            short_win=4,
            long_win=8,
            stable_count=3,
            stability_threshold=0.02,
        )
        # 用递增序列填充窗口，使元素各不相同
        for i in range(12):
            checker.check_stability(100.0 + i * 0.001)
        assert checker.locked
        window_before = list(checker.long_win)
        checker.check_stability(100.0 + 12 * 0.001)
        window_after = list(checker.long_win)
        # 窗口应滚动：最旧元素被移出，最新元素在末尾
        assert window_before[-1] != window_after[-1]
        assert window_before[0] not in window_after
