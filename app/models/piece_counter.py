# app/models/piece_counter.py
from app.models.counter_state import CounterState


# ============================================================
# Threshold Calculation Class
# ============================================================
class Thresholds:
    def __init__(
        self,
        initial_mini_weight: float,
        avg_weight: float,
        tolerance_percent: float,
        min_tol: float,
        dynamic_weight_ratio: float = 0.5,
        initial_min_ratio: float = 0.3,
    ) -> None:
        self.initial_mini_weight: float = initial_mini_weight
        self.avg_weight: float = avg_weight
        self.tolerance_percent: float = tolerance_percent
        self.min_tol: float = min_tol
        self.dynamic_weight_ratio: float = dynamic_weight_ratio
        self.initial_min_ratio: float = initial_min_ratio

    @property
    def dynamic_mini_weight(self) -> float:
        if self.avg_weight <= 0:
            return self.initial_mini_weight
        return max(
            self.avg_weight * self.dynamic_weight_ratio,
            self.initial_mini_weight * self.initial_min_ratio,
        )

    @property
    def recover_threshold(self) -> float:
        """
        Abnormal recovery threshold: avg_weight * tolerance_percent.
        Guaranteed not less than min_tol (to prevent tolerance being too
        small for recovery).
        """
        if self.avg_weight <= 0:
            return max(self.initial_mini_weight, self.min_tol)

        threshold = self.avg_weight * (self.tolerance_percent / 100.0)
        return max(threshold, self.min_tol)

    def update(self, avg_weight: float) -> None:
        self.avg_weight = avg_weight


# ============================================================
# Average Piece Weight Learning Class
# ============================================================
class WeightLearner:
    def __init__(
        self,
        jump_threshold_ratio: float = 0.5,
        jump_confirm_times: int = 2,
        early_learn_pieces: int = 5,
        ema_alpha_min: float = 0.05,
        ema_alpha_max: float = 0.30,
    ) -> None:
        self.jump_threshold_ratio: float = jump_threshold_ratio
        self.jump_confirm_times: int = jump_confirm_times
        self.early_learn_pieces: int = early_learn_pieces
        self.ema_alpha_min: float = ema_alpha_min
        self.ema_alpha_max: float = ema_alpha_max
        self.jump_count: int = 0

    def reset(self) -> None:
        self.jump_count = 0

    def update(
        self, avg_weight: float, piece_weight: float, n: int, total_pieces: int
    ) -> float:
        if total_pieces <= 0:
            return piece_weight

        if total_pieces <= self.early_learn_pieces:
            old_count = total_pieces - n
            if old_count <= 0:
                return piece_weight
            return (avg_weight * old_count + piece_weight * n) / total_pieces

        # ----------- Jump Detection -----------
        if avg_weight > 0:
            diff_ratio = abs(piece_weight - avg_weight) / avg_weight
        else:
            diff_ratio = 1.0

        if diff_ratio > self.jump_threshold_ratio:
            self.jump_count += 1
            if self.jump_count >= self.jump_confirm_times:
                # Trigger Jump: Reset Learning
                self.jump_count = 0
                return piece_weight
        else:
            self.jump_count = 0

        # ----------- Dynamic EMA -----------
        alpha = min(max(diff_ratio, self.ema_alpha_min), self.ema_alpha_max)

        return alpha * piece_weight + (1 - alpha) * avg_weight


# ============================================================
# Tolerance Judgment Class
# ============================================================
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


# ============================================================
# Main Logic Class
# ============================================================


class PieceCounter:
    def __init__(
        self,
        initial_mini_weight: float = 0.5,
        tolerance_percent: float = 20.0,
        stability_threshold: float = 0.02,
        max_batch_pieces: int = 1,
        initial_single_pieces: int = 5,
        decimal_places: int = 2,
        dynamic_weight_ratio: float = 0.5,
        initial_min_ratio: float = 0.3,
        jump_threshold_ratio: float = 0.5,
        jump_confirm_times: int = 2,
        early_learn_pieces: int = 5,
        ema_alpha_min: float = 0.05,
        ema_alpha_max: float = 0.30,
        count_rounding_tolerance: float = 0.2,
        abnormal_recover_factor: float = 1.5,
    ) -> None:

        # Fixed Configuration Parameters
        self.initial_mini_weight: float = initial_mini_weight
        self.max_batch_pieces: int = max_batch_pieces
        self.initial_single_pieces: int = initial_single_pieces
        self.decimal_places: int = decimal_places
        self.count_rounding_tolerance: float = count_rounding_tolerance
        self.abnormal_recover_factor: float = abnormal_recover_factor

        # Calculate min_tol
        resolution: float = 10 ** (-decimal_places)
        min_tol: float = max(resolution * 2, stability_threshold * 2)

        # Utility Classes
        self.tolerance: Tolerance = Tolerance(
            min_tol=min_tol, tolerance_percent=tolerance_percent
        )
        self.learner: WeightLearner = WeightLearner(
            jump_threshold_ratio=jump_threshold_ratio,
            jump_confirm_times=jump_confirm_times,
            early_learn_pieces=early_learn_pieces,
            ema_alpha_min=ema_alpha_min,
            ema_alpha_max=ema_alpha_max,
        )

        # Threshold Management
        self.thresholds: Thresholds = Thresholds(
            initial_mini_weight=initial_mini_weight,
            avg_weight=0.0,
            tolerance_percent=tolerance_percent,
            min_tol=min_tol,
            dynamic_weight_ratio=dynamic_weight_ratio,
            initial_min_ratio=initial_min_ratio,
        )

        self.piece_weights: list[float] = []
        self.last_base_weight: float = 0.0
        self.last_stable_weight: float = 0.0
        self.delta: float = 0.0
        self.state: CounterState = CounterState.ZERO
        self.abnormal_high: bool = False
        self.abnormal_low: bool = False
        self.avg_weight: float = 0.0
        self.abnormal_weight: float = 0.0

        self.reset()

    def reset(self) -> None:
        self.piece_weights = []
        self.last_base_weight = 0.0
        self.last_stable_weight = 0.0

        self.delta = 0.0

        self.state = CounterState.ZERO
        self.abnormal_high = False
        self.abnormal_low = False

        self.avg_weight = 0.0

        self.abnormal_weight = 0.0
        self.learner.reset()
        self._sync_all()

    @property
    def total_pieces(self) -> int:
        return len(self.piece_weights)

    # ---------------------------------------------------------
    # Main Flow
    # ---------------------------------------------------------
    def process(
        self,
        stable_weight: float,
    ) -> None:
        # Jitter Filter for NORMAL/ZERO States
        if self.state != CounterState.ABNORMAL:
            if abs(stable_weight - self.last_stable_weight) < self.tolerance.min_tol:
                self.last_stable_weight = stable_weight
                return

        # Global Zero
        if self._handle_zero_weight(stable_weight):
            return

        # Update Delta
        self._update_delta(stable_weight)

        # State Dispatch
        if self.state == CounterState.ZERO:
            self._handle_zero(stable_weight)

        elif self.state == CounterState.NORMAL:
            self._handle_normal(stable_weight)

        elif self.state == CounterState.ABNORMAL:
            self._handle_abnormal(stable_weight)

    # ---------------------------------------------------------
    # ZERO State: Detect First Piece
    # ---------------------------------------------------------
    def _handle_zero(self, stable_weight: float) -> None:
        if stable_weight < self.thresholds.initial_mini_weight:
            self.last_stable_weight = stable_weight
            return

        # First Piece Established
        if abs(self.delta) >= self.thresholds.initial_mini_weight:
            self._add_pieces(1, self.delta, stable_weight)
            self.state = CounterState.NORMAL

    # ---------------------------------------------------------
    # NORMAL State
    # ---------------------------------------------------------
    def _handle_normal(self, stable_weight: float) -> None:
        # Minimum Effective Change
        if abs(self.delta) < self.thresholds.dynamic_mini_weight:
            self.last_stable_weight = stable_weight
            return

        # Learning phase: can only add 1 piece
        limit = (
            1
            if self.total_pieces < self.initial_single_pieces
            else self.max_batch_pieces
        )

        n = self._try_match_piece_count(self.delta, limit)

        if n is not None:
            if self.delta > 0:
                self._add_pieces(n, self.delta, stable_weight)
            else:
                n_remove = min(n, self.total_pieces)
                if n_remove > 0:
                    self._remove_pieces(n_remove, stable_weight)
        else:
            # Match Failed → Abnormal
            self.state = CounterState.ABNORMAL
            self.abnormal_high = self.delta > 0
            self.abnormal_low = self.delta < 0
            self.abnormal_weight = stable_weight

    # ---------------------------------------------------------
    # ABNORMAL State: Recovery
    # ---------------------------------------------------------
    def _handle_abnormal(self, stable_weight: float) -> None:

        current_delta = stable_weight - self.last_base_weight

        # If direction reverses, update high/low and abnormal reference point
        if current_delta > 0 and not self.abnormal_high:
            self.abnormal_high = True
            self.abnormal_low = False
            self.abnormal_weight = stable_weight

        elif current_delta < 0 and not self.abnormal_low:
            self.abnormal_low = True
            self.abnormal_high = False
            self.abnormal_weight = stable_weight

        # Add-piece abnormal → weight should decrease during recovery
        if self.abnormal_high and stable_weight > self.abnormal_weight:
            self.abnormal_weight = stable_weight
            return

        # Remove-piece abnormal → weight should increase during recovery
        if self.abnormal_low and stable_weight < self.abnormal_weight:
            self.abnormal_weight = stable_weight
            return

        # Must first approach the base point
        # Use 1.5x, leave some margin for physical error
        if (
            abs(current_delta)
            > self.thresholds.recover_threshold * self.abnormal_recover_factor
        ):
            return

        self.clear_abnormal(stable_weight)

    # ---------------------------------------------------------
    # Manually Clear Abnormal
    # ---------------------------------------------------------
    def clear_abnormal(self, stable_weight: float) -> None:
        if self.state == CounterState.ABNORMAL:
            self.state = CounterState.NORMAL
            self.abnormal_high = False
            self.abnormal_low = False
            self.abnormal_weight = 0.0
            self.last_stable_weight = stable_weight
            self.last_base_weight = stable_weight

    # ---------------------------------------------------------
    # Force Calibration
    # ---------------------------------------------------------
    def force_accept(self, stable_weight: float, force_pieces: int) -> None:
        if stable_weight < self.thresholds.initial_mini_weight or force_pieces <= 0:
            return

        # Rebuild Model
        self.piece_weights.clear()
        piece_weight = stable_weight / force_pieces
        for _ in range(force_pieces):
            self.piece_weights.append(piece_weight)

        self.avg_weight = piece_weight
        self._sync_all()

        self.clear_abnormal(stable_weight)

    # ---------------------------------------------------------
    # Utility Functions
    # ---------------------------------------------------------
    def _handle_zero_weight(self, stable_weight: float) -> bool:
        # Global Zero: Regardless of state, reset when weight drops to zero
        if stable_weight < self.thresholds.initial_mini_weight:
            self.reset()
            self.last_base_weight = stable_weight
            self.last_stable_weight = stable_weight
            return True
        return False

    def _update_delta(self, stable_weight: float) -> None:
        self.delta = stable_weight - self.last_base_weight

    def _try_match_piece_count(self, delta: float, limit: int) -> int | None:
        if self.avg_weight <= 0:
            return None

        n_est = abs(delta) / self.avg_weight
        n = int(round(n_est))

        if not (1 <= n <= limit):
            return None

        if abs(n_est - n) > self.count_rounding_tolerance:
            return None

        # Tolerance Check
        if not self.tolerance.is_within_tolerance(abs(delta), n):
            return None

        return n

    # ---------------------------------------------------------
    # Add Piece / Remove Piece
    # ---------------------------------------------------------
    def _add_pieces(self, n: int, delta: float, stable_weight: float) -> None:
        piece_weight = delta / n
        for _ in range(n):
            self.piece_weights.append(piece_weight)

        # Update Average Piece Weight
        self.avg_weight = self.learner.update(
            self.avg_weight, piece_weight, n, self.total_pieces
        )
        self._sync_all()

        # Only update when this weight is truly accepted
        self.last_base_weight = stable_weight
        self.last_stable_weight = stable_weight

    def _remove_pieces(self, n: int, stable_weight: float) -> None:
        del self.piece_weights[-n:]
        if not self.piece_weights:
            self.avg_weight = 0.0
        else:
            self.avg_weight = sum(self.piece_weights) / len(self.piece_weights)
        self._sync_all()

        # Only update when this weight is truly accepted
        self.last_base_weight = stable_weight
        self.last_stable_weight = stable_weight

    def _sync_all(self) -> None:
        self.thresholds.update(self.avg_weight)
        self.tolerance.update(self.avg_weight)

    def set_initial_single_pieces(self, initial_single_pieces: int) -> None:
        if initial_single_pieces > 0:
            self.initial_single_pieces = initial_single_pieces

    def set_max_batch_pieces(self, max_batch_pieces: int) -> None:
        if max_batch_pieces > 0:
            self.max_batch_pieces = max_batch_pieces

    def set_tolerance_percent(self, tolerance_percent: float) -> None:
        if 0.0 < tolerance_percent < 100.0:
            self.tolerance.tolerance_percent = tolerance_percent
            self.thresholds.tolerance_percent = tolerance_percent
            self._sync_all()
