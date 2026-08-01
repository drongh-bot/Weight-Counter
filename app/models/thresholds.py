# app/models/thresholds.py


class Thresholds:
    def __init__(
        self,
        initial_min_weight: float,
        avg_weight: float,
        tolerance_percent: float,
        min_tol: float,
        dynamic_weight_ratio: float = 0.5,
        initial_min_ratio: float = 0.3,
    ) -> None:
        self.initial_min_weight: float = initial_min_weight
        self.avg_weight: float = avg_weight
        self.tolerance_percent: float = tolerance_percent
        self.min_tol: float = min_tol
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

    @property
    def recover_threshold(self) -> float:
        """
        Abnormal recovery threshold: avg_weight * tolerance_percent.
        Guaranteed not less than min_tol (to prevent tolerance being too
        small for recovery).
        """
        if self.avg_weight <= 0:
            return max(self.initial_min_weight, self.min_tol)

        threshold = self.avg_weight * (self.tolerance_percent / 100.0)
        return max(threshold, self.min_tol)

    def update(self, avg_weight: float) -> None:
        self.avg_weight = avg_weight
