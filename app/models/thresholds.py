# app/models/thresholds.py


class Thresholds:
    """动态最小重量阈值。avg 在调用时传入。"""

    def __init__(
        self,
        initial_min_weight: float,
        dynamic_weight_ratio: float = 0.5,
        initial_min_ratio: float = 0.3,
    ) -> None:
        """保存动态最小重量相关配置。"""
        self.initial_min_weight: float = initial_min_weight
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
