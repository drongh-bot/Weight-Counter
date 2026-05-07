# app/services/counter_service.py

from PySide6.QtCore import QObject

from app.models.biz_result import BizResult, BizState
from app.models.params import Params
from app.models.piece_counter import CounterState, PieceCounter


class CounterService(QObject):
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
        super().__init__()

        self.params = params

        # edge trigger flags
        self.abnormal_edge = False
        self.target_edge = False
        self.prev_reached_target = False

        # core counter
        self.counter = PieceCounter(
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
        self.counter.set_initial_single_pieces(self.params.initial_single_pieces)
        self.counter.set_max_batch_pieces(self.params.max_batch_pieces)
        self.counter.set_tolerance_percent(self.params.tolerance_percent)

    # ============================================================
    # Core: process stable weight (event result)
    # ============================================================
    def process(self, stable_weight: float) -> BizResult:
        old_count = self.counter.total_pieces
        old_state = self.counter.state

        # process weight
        self.counter.process(stable_weight)

        new_count = self.counter.total_pieces
        new_state = self.counter.state

        # -------------------------
        # Abnormal edge trigger
        # -------------------------
        self.abnormal_edge = (
            old_state != CounterState.ABNORMAL and new_state == CounterState.ABNORMAL
        )

        # -------------------------
        # Target edge trigger
        # -------------------------
        target = self.params.target_pieces
        curr_reached = 0 < target == new_count and new_state == CounterState.NORMAL
        self.target_edge = (not self.prev_reached_target) and curr_reached
        self.prev_reached_target = curr_reached

        # -------------------------
        # Whether added in this cycle
        # -------------------------
        added = new_count > old_count

        # -------------------------
        # Return event result
        # -------------------------
        return self._build_result(added=added)

    # ============================================================
    # State mapping + result construction
    # ============================================================
    @staticmethod
    def _map_state(state: CounterState) -> BizState:
        if state == CounterState.ZERO:
            return BizState.ZERO
        if state == CounterState.NORMAL:
            return BizState.NORMAL
        return BizState.ABNORMAL

    def _build_result(self, added: bool = False) -> BizResult:
        return BizResult(
            added=added,
            abnormal_high=self.counter.high,
            abnormal_low=self.counter.low,
            state=self._map_state(self.counter.state),
            delta=self.counter.delta,
            avg_weight=self.counter.avg_weight,
            tol_high=self.counter.tolerance.high,
            tol_low=self.counter.tolerance.low,
            total_pieces=self.counter.total_pieces,
            last_stable_weight=self.counter.last_stable_weight,
            last_base_weight=self.counter.last_base_weight,
            weights=self.counter.piece_weights,
            decimal_places=self.counter.decimal_places,
        )

    # ============================================================
    # Force accept / Clear abnormal
    # ============================================================
    def force_accept(self, stable_weight: float, pieces: int) -> None:
        self.counter.force_accept(stable_weight, pieces)

    def clear_abnormal(self, stable_weight: float) -> None:
        self.counter.clear_abnormal(stable_weight)

    # ============================================================
    # Reset
    # ============================================================
    def reset(self) -> None:
        self.counter.reset()
        self.abnormal_edge = False
        self.target_edge = False
        self.prev_reached_target = False

    # ============================================================
    # Edge flag consumption (read-then-clear, decouples external raw assignment)
    # ============================================================
    def consume_abnormal_edge(self) -> bool:
        result = self.abnormal_edge
        self.abnormal_edge = False
        return result

    def consume_target_edge(self) -> bool:
        result = self.target_edge
        self.target_edge = False
        return result

    # ============================================================
    # Current business state (does not count, only returns current state)
    # ============================================================
    def current_result(self) -> BizResult:
        return self._build_result()
