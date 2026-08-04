# app/models/tolerance.py


class Tolerance:
    """单件公差带 + sqrt(n) 批量判定。调用时传入 avg_weight（不缓存）。"""

    def __init__(self, min_tol: float, tolerance_percent: float) -> None:
        """保存最小公差与百分比配置。"""
        self.min_tol: float = min_tol
        self.tolerance_percent: float = tolerance_percent

    def band(self, avg_weight: float) -> tuple[float, float, float]:
        """返回给定平均单重的 (下限, 上限, 半宽)。"""
        if avg_weight <= 0:
            return 0.0, 0.0, 0.0

        tol = self.tolerance_percent / 100.0
        low = avg_weight * (1 - tol)
        high = avg_weight * (1 + tol)

        # 至少向外扩展 min_tol
        low = min(low, avg_weight - self.min_tol)
        high = max(high, avg_weight + self.min_tol)
        half_range = max(avg_weight - low, high - avg_weight)
        return low, high, half_range

    def is_within_tolerance(
        self, delta_abs: float, n: int, avg_weight: float
    ) -> bool:
        """sqrt(n) 公差模型：基于统计的总重判定。"""
        if avg_weight <= 0:
            return False

        _, _, half_range = self.band(avg_weight)
        if half_range <= 0:
            return False

        expected_total = avg_weight * n
        allowed_error = half_range * (n**0.5)
        return abs(delta_abs - expected_total) <= allowed_error
