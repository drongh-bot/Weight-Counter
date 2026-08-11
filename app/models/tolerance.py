# app/models/tolerance.py

from dataclasses import dataclass


@dataclass(frozen=True)
class ToleranceBand:
    """单件公差带：下限、上限、半宽。"""

    low: float
    high: float
    half_range: float


class Tolerance:
    """单件公差带 + sqrt(n) 批量判定。avg 与百分比在调用时传入。"""

    def __init__(self, min_tol: float) -> None:
        """保存最小公差（分辨率相关）。"""
        self.min_tol: float = min_tol

    def band(self, avg_weight: float, tolerance_percent: float) -> ToleranceBand:
        """返回给定平均单重与百分比的公差带。"""
        if avg_weight <= 0:
            return ToleranceBand(0.0, 0.0, 0.0)

        tol = tolerance_percent / 100.0
        low = avg_weight * (1 - tol)
        high = avg_weight * (1 + tol)

        # 至少向外扩展 min_tol
        low = min(low, avg_weight - self.min_tol)
        high = max(high, avg_weight + self.min_tol)
        half_range = max(avg_weight - low, high - avg_weight)
        return ToleranceBand(low=low, high=high, half_range=half_range)

    def is_within_tolerance(
        self,
        delta_abs: float,
        n: int,
        avg_weight: float,
        tolerance_percent: float,
    ) -> bool:
        """sqrt(n) 公差模型：基于统计的总重判定。"""
        if avg_weight <= 0:
            return False

        half_range = self.band(avg_weight, tolerance_percent).half_range
        if half_range <= 0:
            return False

        expected_total = avg_weight * n
        allowed_error = half_range * (n**0.5)
        return abs(delta_abs - expected_total) <= allowed_error
