# app/models/tolerance.py


class Tolerance:
    def __init__(self, min_tol: float, tolerance_percent: float) -> None:
        self.min_tol: float = min_tol
        self.low: float = 0.0
        self.high: float = 0.0
        self.tolerance_percent: float = tolerance_percent
        self.current_avg: float = 0.0
        self.half_range: float = 0.0

    def update(self, avg_weight: float) -> None:
        """
        Update tolerance range and cache avg_weight and half_range.
        """
        self.current_avg = avg_weight

        if avg_weight <= 0:
            self.low = 0
            self.high = 0
            self.half_range = 0
            return

        tol = self.tolerance_percent / 100.0

        # Linear Tolerance Range (Single Piece)
        low = avg_weight * (1 - tol)
        high = avg_weight * (1 + tol)

        # Add min_tol (Prevent Tolerance Too Small)
        # Extend tolerance range outward by at least min_tol
        self.low = min(
            low, avg_weight - self.min_tol
        )  # Lower bound smaller (wider tolerance)
        self.high = max(
            high, avg_weight + self.min_tol
        )  # Upper bound larger (wider tolerance)

        # Single Piece Error (Take the Larger Side)
        self.half_range = max(avg_weight - self.low, self.high - avg_weight)

    def is_within_tolerance(self, delta_abs: float, n: int) -> bool:
        """
        sqrt(n) tolerance model: statistics-based total weight judgment
        """
        if self.current_avg <= 0 or self.half_range <= 0:
            return False

        expected_total = self.current_avg * n
        allowed_error = self.half_range * (n**0.5)

        return abs(delta_abs - expected_total) <= allowed_error
