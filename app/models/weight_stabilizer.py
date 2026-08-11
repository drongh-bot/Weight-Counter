# app/models/weight_stabilizer.py
import statistics
from collections import deque

from app.models.params import Params


class WeightStabilizer:
    """
    工业级稳定性检测器
    - 统一阈值体系
    - 稳定锁定 + 解锁迟滞
    - 多帧解锁确认
    - 前几帧不参与判定
    """

    def __init__(
        self,
        short_maxlen: int = 5,
        long_maxlen: int = 10,
        stable_count: int = 3,
        unlock_confirm: int = 2,
        unlock_factor: float = 2.5,
        stability_threshold: float = 0.02,
    ) -> None:
        """初始化双滑动窗口与锁定/解锁参数。"""
        self.short_win: deque[float] = deque(maxlen=short_maxlen)
        self.long_win: deque[float] = deque(maxlen=long_maxlen)
        self.stable_count_required: int = stable_count
        self.stable_counter: int = 0
        self.locked: bool = False
        self.locked_weight: float | None = None
        self.unlock_factor: float = unlock_factor
        self.unlock_confirm_required: int = unlock_confirm
        self.unlock_pending: int = 0
        self.stability_threshold: float = stability_threshold

    def apply_start_params(self, params: Params) -> None:
        """从共享 Params 复制稳定阈值（点 Start 才生效）。"""
        if params.stability_threshold > 0:
            self.stability_threshold = params.stability_threshold

    def reset(self) -> None:
        """清空窗口与锁定状态。"""
        self.short_win.clear()
        self.long_win.clear()
        self.stable_counter = 0
        self.locked = False
        self.locked_weight = None
        self.unlock_pending = 0

    def stabilize(self, weight: float) -> float | None:
        """
        输入：当前重量
        输出：稳定重量（None 表示未稳定）
        """
        eps = 1e-6
        stability_threshold = max(self.stability_threshold, eps)

        self.short_win.append(weight)
        self.long_win.append(weight)

        if self.locked:
            locked_weight = self.locked_weight
            if locked_weight is None:
                self.locked = False
                self.unlock_pending = 0
                self.stable_counter = 0
            else:
                unlock_threshold = stability_threshold * self.unlock_factor

                if abs(weight - locked_weight) > unlock_threshold:
                    self.unlock_pending += 1
                else:
                    self.unlock_pending = 0

                if self.unlock_pending >= self.unlock_confirm_required:
                    self.locked = False
                    self.locked_weight = None
                    self.unlock_pending = 0
                    self.stable_counter = 0
                else:
                    return locked_weight

        long_maxlen = self.long_win.maxlen
        if long_maxlen is None or len(self.long_win) < long_maxlen:
            self.stable_counter = 0
            return None

        dynamic_threshold = max(stability_threshold, abs(weight) * 0.001, eps)
        speed_limit = dynamic_threshold
        trend_limit = dynamic_threshold * 1.5
        std_limit = dynamic_threshold * 1.2

        if (max(self.short_win) - min(self.short_win)) > speed_limit:
            self.stable_counter = 0
            return None

        if (max(self.long_win) - min(self.long_win)) > trend_limit:
            self.stable_counter = 0
            return None

        if statistics.stdev(self.long_win) > std_limit:
            self.stable_counter = 0
            return None

        self.stable_counter += 1
        if self.stable_counter < self.stable_count_required:
            return None

        stable_weight = statistics.median(self.long_win)
        self.locked = True
        self.locked_weight = stable_weight
        return stable_weight
