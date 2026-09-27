# app/models/tolerance.py

from dataclasses import dataclass


@dataclass(frozen=True)
class ToleranceBand:
    """单件公差带：下限、上限、半宽。"""

    low: float
    high: float
    half_range: float


class Tolerance:
    """单件公差规则：公差带 + sqrt(n) 批量判定。

    公差的两个参数（``min_tol`` 与 ``tolerance_percent``）都住在这里，
    外部只通过 ``set_percent`` / ``recalc_min_tol`` 改，不直接写属性。
    """

    def __init__(self, min_tol: float, tolerance_percent: float) -> None:
        """保存最小公差（分辨率相关）与公差百分比。"""
        self.min_tol: float = min_tol
        self.tolerance_percent: float = tolerance_percent

    def set_percent(self, value: float) -> None:
        """更新公差百分比；非法值（手改 config.toml 可能给）保留当前值。"""
        if 0.0 < value < 100.0:
            self.tolerance_percent = value

    def band(self, avg_weight: float) -> ToleranceBand:
        """返回给定平均单重的公差带。"""
        if avg_weight <= 0:
            return ToleranceBand(0.0, 0.0, 0.0)

        tol = self.tolerance_percent / 100.0
        low = avg_weight * (1 - tol)
        high = avg_weight * (1 + tol)

        # 至少向外扩展 min_tol
        low = min(low, avg_weight - self.min_tol)
        high = max(high, avg_weight + self.min_tol)
        half_range = max(avg_weight - low, high - avg_weight)
        return ToleranceBand(low=low, high=high, half_range=half_range)

    def is_within_tolerance(self, delta_abs: float, n: int, avg_weight: float) -> bool:
        """sqrt(n) 公差模型：基于统计的总重判定。"""
        if avg_weight <= 0:
            return False

        half_range = self.band(avg_weight).half_range
        if half_range <= 0:
            return False

        expected_total = avg_weight * n
        allowed_error = half_range * (n**0.5)
        return abs(delta_abs - expected_total) <= allowed_error
