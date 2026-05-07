# app/models/weight_stability_checker.py
import statistics
from collections import deque


class WeightStabilityChecker:
    """
    Industrial-grade stability detector (enhanced version)
    - Unified threshold system
    - Stable lock + unlock hysteresis
    - Multi-frame unlock confirmation
    - First few frames excluded from judgment
    """

    def __init__(
        self,
        short_win: int = 5,
        long_win: int = 10,
        stable_count: int = 3,
        unlock_confirm: int = 2,
        unlock_factor: float = 2.5,
        base_threshold: float = 0.02,
    ) -> None:
        # Windows
        self.short_win: deque[float] = deque(maxlen=short_win)
        self.long_win: deque[float] = deque(maxlen=long_win)

        # Stable Count
        self.stable_count_required: int = stable_count
        self.stable_counter: int = 0

        # Lock Mode
        self.locked: bool = False
        self.locked_weight: float | None = None

        # Unlock Mechanism
        self.unlock_factor: float = unlock_factor
        self.unlock_confirm_required: int = unlock_confirm
        self.unlock_pending: int = 0

        # Threshold
        self.base_threshold: float = base_threshold

        # Output Cache
        self.last_stable_weight: float | None = None

    # ============================================================
    # Hot Update Parameters
    # ============================================================
    def set_base_threshold(self, base_threshold: float) -> None:
        if base_threshold > 0:
            self.base_threshold = base_threshold

    def set_stable_count(self, stable_count: int) -> None:
        if stable_count > 0:
            self.stable_count_required = stable_count

    # ============================================================
    # Reset
    # ============================================================
    def reset(self) -> None:
        self.short_win.clear()
        self.long_win.clear()
        self.stable_counter = 0

        self.locked = False
        self.locked_weight = None
        self.unlock_pending = 0

        self.last_stable_weight = None

    # ============================================================
    # Main Logic
    # ============================================================
    def update(self, weight: float) -> float | None:
        """
        Input: current weight
        Output: stable weight (None means unstable)
        """
        eps = 1e-6
        base_threshold = max(self.base_threshold, eps)

        # Update Windows
        self.short_win.append(weight)
        self.long_win.append(weight)

        # ============================================================
        # 1. Lock Mode (with hysteresis + multi-frame unlock confirmation)
        # Keep updating windows during lock to ensure data is fresh after unlock
        # ============================================================

        if self.locked:
            unlock_threshold = base_threshold * self.unlock_factor

            assert self.locked_weight is not None
            if abs(weight - self.locked_weight) > unlock_threshold:
                # Exceeded unlock threshold, increment confirmation count
                self.unlock_pending += 1

                if self.unlock_pending >= self.unlock_confirm_required:
                    # Actually Unlock
                    self.locked = False
                    self.locked_weight = None
                    self.unlock_pending = 0
                    self.stable_counter = 0
                else:
                    # Still Remain Locked
                    self.last_stable_weight = self.locked_weight
                    return self.locked_weight
            else:
                # Not exceeded unlock threshold, clear pending
                self.unlock_pending = 0
                self.last_stable_weight = self.locked_weight
                return self.locked_weight

        # ============================================================
        # 2. Normal Stability Detection
        # ============================================================

        # Skip early frames (common practice in industrial weighing)
        assert self.long_win.maxlen is not None
        if len(self.long_win) < self.long_win.maxlen:
            self.stable_counter = 0
            return None

        # Unified Threshold System
        dynamic_threshold = max(base_threshold, abs(weight) * 0.001, eps)
        speed_limit = dynamic_threshold
        trend_limit = dynamic_threshold * 1.5
        std_limit = dynamic_threshold * 1.2

        # -----------------------------
        # Speed Detection (short window)
        # -----------------------------
        if (max(self.short_win) - min(self.short_win)) > speed_limit:
            self.stable_counter = 0
            return None

        # -----------------------------
        # Trend Detection (long window)
        # -----------------------------
        span = max(self.long_win) - min(self.long_win)
        if span > trend_limit:
            self.stable_counter = 0
            return None

        # -----------------------------
        # Standard Deviation Detection (long window)
        # -----------------------------
        std_val = statistics.stdev(self.long_win)
        if std_val > std_limit:
            self.stable_counter = 0
            return None

        # ============================================================
        # Consecutive Stable Count
        # ============================================================
        self.stable_counter += 1
        if self.stable_counter < self.stable_count_required:
            return None

        # ============================================================
        # Enter Stable Lock
        # ============================================================
        stable_weight = statistics.median(self.long_win)

        self.locked = True
        self.locked_weight = stable_weight

        self.last_stable_weight = stable_weight

        return stable_weight
