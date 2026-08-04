# app/models/thresholds.py


class Thresholds:
    """动态最小重量 / 异常恢复阈值。avg 与百分比在调用时传入。"""

    def __init__(
        self,
        initial_min_weight: float,
        min_tol: float,
        dynamic_weight_ratio: float = 0.5,
        initial_min_ratio: float = 0.3,
    ) -> None:
        """保存阈值计算所需的配置字段（不含公差百分比）。"""
        self.initial_min_weight: float = initial_min_weight
        self.min_tol: float = min_tol
        self.dynamic_weight_ratio: float = dynamic_weight_ratio
        self.initial_min_ratio: float = initial_min_ratio

    def dynamic_min_weight(self, avg_weight: float) -> float:
        """计件触发所需的最小 delta 阈值。"""
        if avg_weight <= 0:
            return self.initial_min_weight
        return max(
            avg_weight * self.dynamic_weight_ratio,
            self.initial_min_weight * self.initial_min_ratio,
        )

    def recover_threshold(
        self, avg_weight: float, tolerance_percent: float
    ) -> float:
        """异常恢复阈值：avg × 公差%，至少 min_tol。"""
        if avg_weight <= 0:
            return max(self.initial_min_weight, self.min_tol)

        threshold = avg_weight * (tolerance_percent / 100.0)
        return max(threshold, self.min_tol)
