from app.models.weight_stabilizer import WeightStabilizer


class TestStableDetection:
    def test_stable_after_consecutive_frames(self):
        """连续 stable_count 帧稳定后返回稳定值"""
        stabilizer = WeightStabilizer(
            short_maxlen=4,
            long_maxlen=8,
            stable_count=3,
            stability_threshold=0.02,
        )
        value = 100.0
        # 前 7 帧填充长窗口，返回 None
        for _ in range(stabilizer.long_win.maxlen - 1):
            result = stabilizer.stabilize(value)
            assert result is None
        # 连续 3 帧稳定后进入锁定
        for i in range(stabilizer.stable_count_required):
            result = stabilizer.stabilize(value)
            if i < stabilizer.stable_count_required - 1:
                assert result is None
            else:
                assert result is not None

    def test_unstable_by_speed(self):
        """短窗口内快速变化 → 不稳定"""
        stabilizer = WeightStabilizer(
            short_maxlen=4,
            long_maxlen=8,
            stable_count=3,
            stability_threshold=0.02,
        )
        # 先填充窗口
        for _ in range(8):
            stabilizer.stabilize(100.0)
        # 突变超过 speed_limit
        result = stabilizer.stabilize(110.0)
        assert result is None

    def test_unstable_by_trend(self):
        """长窗口内持续漂移 → 不稳定"""
        stabilizer = WeightStabilizer(
            short_maxlen=4,
            long_maxlen=8,
            stable_count=3,
            stability_threshold=0.02,
        )
        # 逐步上升
        for i in range(8):
            stabilizer.stabilize(100.0 + i * 0.5)
        # 漂移超过 trend_limit
        result = stabilizer.stabilize(105.0)
        assert result is None

    def test_unstable_by_stddev(self):
        """长窗口内方差过大 → 不稳定"""
        stabilizer = WeightStabilizer(
            short_maxlen=4,
            long_maxlen=8,
            stable_count=3,
            stability_threshold=0.02,
        )
        values = [100.0, 100.5, 99.5, 101.0, 98.0, 102.0, 100.0, 101.5]
        for v in values:
            stabilizer.stabilize(v)
        result = stabilizer.stabilize(97.0)
        assert result is None


class TestLockAndUnlock:
    def test_lock_after_stable(self):
        """稳定后锁定，持续返回稳定值"""
        stabilizer = WeightStabilizer(
            short_maxlen=4,
            long_maxlen=8,
            stable_count=3,
            stability_threshold=0.02,
            unlock_factor=2.5,
        )
        value = 50.0
        for _ in range(10):
            stabilizer.stabilize(value)
        # 锁定后无论继续喂相同值都返回稳定值
        for _ in range(5):
            result = stabilizer.stabilize(value)
            assert result is not None

    def test_unlock_after_exceeding_threshold(self):
        """超过解锁阈值，连续 unlock_confirm 帧后解锁"""
        stabilizer = WeightStabilizer(
            short_maxlen=4,
            long_maxlen=8,
            stable_count=3,
            unlock_confirm=2,
            unlock_factor=2.5,
            stability_threshold=0.02,
        )
        value = 50.0
        for _ in range(10):
            stabilizer.stabilize(value)
        # 锁定中
        assert stabilizer.locked
        # 突变超过锁定值 + unlock_factor * stability_threshold
        jump = 50.0 + 2.5 * 0.02 + 0.01
        # 第一帧仍锁定
        result = stabilizer.stabilize(jump)
        assert stabilizer.locked
        assert result is not None
        # 第二帧解锁
        result = stabilizer.stabilize(jump)
        assert not stabilizer.locked

    def test_no_unlock_on_minor_change(self):
        """小幅波动不足解锁阈值，保持锁定"""
        stabilizer = WeightStabilizer(
            short_maxlen=4,
            long_maxlen=8,
            stable_count=3,
            unlock_factor=2.5,
            stability_threshold=0.02,
        )
        value = 50.0
        for _ in range(10):
            stabilizer.stabilize(value)
        # 小幅变化，不应解锁
        for _ in range(5):
            result = stabilizer.stabilize(value + 0.01)
            assert stabilizer.locked
            assert result is not None


class TestEdgeCases:
    def test_early_frame_skip(self):
        """长窗口未满时不判定稳定"""
        stabilizer = WeightStabilizer(
            short_maxlen=4,
            long_maxlen=8,
            stable_count=3,
        )
        for _ in range(5):
            result = stabilizer.stabilize(10.0)
            assert result is None

    def test_reset(self):
        """reset 清空所有状态"""
        stabilizer = WeightStabilizer(short_maxlen=4, long_maxlen=8)
        for _ in range(15):
            stabilizer.stabilize(42.0)
        assert stabilizer.locked
        stabilizer.reset()
        assert not stabilizer.locked
        assert stabilizer.locked_weight is None
        assert len(stabilizer.short_win) == 0
        assert len(stabilizer.long_win) == 0
        assert stabilizer.stable_counter == 0

    def test_apply_start_params_threshold(self):
        """apply_start_params 将 stability_threshold 复制进实例"""
        from app.models.params import Params

        stabilizer = WeightStabilizer(stability_threshold=10.0)
        stabilizer.apply_start_params(Params(stability_threshold=0.001))
        assert stabilizer.stability_threshold == 0.001

    def test_stable_count_from_constructor(self):
        """stable_count 在构造时设定（启动期窗口参数）"""
        stabilizer = WeightStabilizer(stable_count=5)
        assert stabilizer.stable_count_required == 5

    def test_lock_keeps_updating_windows(self):
        """锁定期间窗口持续滚动更新"""
        stabilizer = WeightStabilizer(
            short_maxlen=4,
            long_maxlen=8,
            stable_count=3,
            stability_threshold=0.02,
        )
        # 用递增序列填充窗口，使元素各不相同
        for i in range(12):
            stabilizer.stabilize(100.0 + i * 0.001)
        assert stabilizer.locked
        window_before = list(stabilizer.long_win)
        stabilizer.stabilize(100.0 + 12 * 0.001)
        window_after = list(stabilizer.long_win)
        # 窗口应滚动：最旧元素被移出，最新元素在末尾
        assert window_before[-1] != window_after[-1]
        assert window_before[0] not in window_after
