# app/services/counter_service.py

from app.models.biz_result import BizResult
from app.models.params import Params
from app.models.counter_state import CounterState
from app.models.piece_counter import PieceCounter


class CounterService:
    """
    Counting business service

    Responsibilities:
    - Feed stable weight into PieceCounter for counting
    - Detect abnormal/target edge triggers (rising edge)
    - Map CounterState to BizState
    - Build BizResult (unified data carrier)
    - Force accept, clear abnormal, reset
    - Consume edge flags (consume_*), avoiding external direct state manipulation
    """

    def __init__(self, params: Params) -> None:
        self.params = params

        # edge trigger flags
        self._abnormal_edge = False
        self._target_edge = False
        self._previously_reached_target = False

        # core counter
        self._piece_counter = PieceCounter(
            initial_mini_weight=params.initial_mini_weight,
            tolerance_percent=params.tolerance_percent,
            stability_threshold=params.stability_threshold,
            max_batch_pieces=params.max_batch_pieces,
            initial_single_pieces=params.initial_single_pieces,
            decimal_places=params.decimal_places,
            dynamic_weight_ratio=params.dynamic_weight_ratio,
            initial_min_ratio=params.initial_min_ratio,
            jump_threshold_ratio=params.jump_threshold_ratio,
            jump_confirm_times=params.jump_confirm_times,
            early_learn_pieces=params.early_learn_pieces,
            ema_alpha_min=params.ema_alpha_min,
            ema_alpha_max=params.ema_alpha_max,
            count_rounding_tolerance=params.count_rounding_tolerance,
            abnormal_recover_factor=params.abnormal_recover_factor,
        )

    # ============================================================
    # Parameter update
    # ============================================================
    def apply_params(self) -> None:
        self._piece_counter.set_initial_single_pieces(self.params.initial_single_pieces)
        self._piece_counter.set_max_batch_pieces(self.params.max_batch_pieces)
        self._piece_counter.set_tolerance_percent(self.params.tolerance_percent)

    # ============================================================
    # Core: process stable weight (event result)
    # ============================================================
    def process(self, stable_weight: float) -> BizResult:
        old_count = self._piece_counter.total_pieces
        old_state = self._piece_counter.state

        # process weight
        self._piece_counter.process(stable_weight)

        new_count = self._piece_counter.total_pieces
        new_state = self._piece_counter.state

        # -------------------------
        # Abnormal edge trigger
        # -------------------------
        self._abnormal_edge = (
            old_state != CounterState.ABNORMAL and new_state == CounterState.ABNORMAL
        )

        # -------------------------
        # Target edge trigger
        # -------------------------
        target = self.params.target_pieces
        reached = 0 < target == new_count and new_state == CounterState.NORMAL
        self._target_edge = (not self._previously_reached_target) and reached
        self._previously_reached_target = reached

        # -------------------------
        # Whether added in this cycle
        # -------------------------
        added = new_count > old_count

        # -------------------------
        # Return event result
        # -------------------------
        return self._build_result(added=added)

    # ============================================================
    # Result construction
    # ============================================================
    def _build_result(self, added: bool = False) -> BizResult:
        return BizResult(
            added=added,
            abnormal_high=self._piece_counter.abnormal_high,
            abnormal_low=self._piece_counter.abnormal_low,
            state=self._piece_counter.state,
            delta=self._piece_counter.delta,
            avg_weight=self._piece_counter.avg_weight,
            tol_high=self._piece_counter.tolerance.high,
            tol_low=self._piece_counter.tolerance.low,
            total_pieces=self._piece_counter.total_pieces,
            last_stable_weight=self._piece_counter.last_stable_weight,
            last_base_weight=self._piece_counter.last_base_weight,
            weights=self._piece_counter.piece_weights,
            decimal_places=self._piece_counter.decimal_places,
        )

    # ============================================================
    # Force accept / Clear abnormal
    # ============================================================
    def force_accept(self, stable_weight: float, pieces: int) -> None:
        self._piece_counter.force_accept(stable_weight, pieces)

    def clear_abnormal(self, stable_weight: float) -> None:
        self._piece_counter.clear_abnormal(stable_weight)

    # ============================================================
    # Reset
    # ============================================================
    def reset(self) -> None:
        self._piece_counter.reset()
        self._abnormal_edge = False
        self._target_edge = False
        self._previously_reached_target = False

    # ============================================================
    # Edge flag consumption (read-then-clear, decouples external raw assignment)
    # ============================================================
    def consume_abnormal_edge(self) -> bool:
        result = self._abnormal_edge
        self._abnormal_edge = False
        return result

    def consume_target_edge(self) -> bool:
        result = self._target_edge
        self._target_edge = False
        return result

    # ============================================================
    # Current business state (does not count, only returns current state)
    # ============================================================
    def current_result(self) -> BizResult:
        return self._build_result()
