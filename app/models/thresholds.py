# app/models/thresholds.py


class Thresholds:
    """动态最小重量阈值。avg 经 update() 同步。"""

    def __init__(
        self,
        initial_min_weight: float,
        avg_weight: float,
        dynamic_weight_ratio: float = 0.5,
        initial_min_ratio: float = 0.3,
    ) -> None:
        self.initial_min_weight: float = initial_min_weight
        self.avg_weight: float = avg_weight
        self.dynamic_weight_ratio: float = dynamic_weight_ratio
        self.initial_min_ratio: float = initial_min_ratio

    @property
    def dynamic_min_weight(self) -> float:
        if self.avg_weight <= 0:
            return self.initial_min_weight
        return max(
            self.avg_weight * self.dynamic_weight_ratio,
            self.initial_min_weight * self.initial_min_ratio,
        )

    def update(self, avg_weight: float) -> None:
        self.avg_weight = avg_weight
