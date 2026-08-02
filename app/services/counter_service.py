# app/services/counter_service.py

from app.models.count_result import CountResult
from app.models.params import Params
from app.models.counter_state import CounterState
from app.models.piece_counter import PieceCounter


class CounterService:
    """
    Counting business service

    Responsibilities:
    - Feed stable weight into PieceCounter for counting
    - Detect abnormal/target edge triggers (rising edge)
    - Build CountResult (unified data carrier)
    - Force calibrate, reset
    - Consume edge flags (consume_*), avoiding external direct state manipulation
    """

    def __init__(self, params: Params) -> None:
        self.params = params
        self._abnormal_edge = False
        self._target_edge = False
        self._piece_counter = PieceCounter.from_params(params)

    def apply_start_params(self) -> None:
        self._piece_counter.apply_start_params(self.params)

    def _mark_target_edge_if_crossed(
        self, old_count: int, new_count: int, state: CounterState
    ) -> None:
        target = self.params.target_pieces
        if (
            0 < target
            and old_count < target <= new_count
            and state == CounterState.NORMAL
        ):
            self._target_edge = True

    def process(self, stable_weight: float) -> CountResult:
        old_count = self._piece_counter.total_pieces
        old_state = self._piece_counter.state

        self._piece_counter.process(stable_weight)

        new_count = self._piece_counter.total_pieces
        new_state = self._piece_counter.state

        self._abnormal_edge = (
            old_state != CounterState.ABNORMAL and new_state == CounterState.ABNORMAL
        )
        self._mark_target_edge_if_crossed(old_count, new_count, new_state)
        added = new_count > old_count
        return self._build_result(added=added)

    def _build_result(self, added: bool = False) -> CountResult:
        return CountResult(
            added=added,
            abnormal_high=self._piece_counter.abnormal_high,
            abnormal_low=self._piece_counter.abnormal_low,
            state=self._piece_counter.state,
            delta=self._piece_counter.delta,
            avg_weight=self._piece_counter.avg_weight,
            tolerance_high=self._piece_counter.tolerance.high,
            tolerance_low=self._piece_counter.tolerance.low,
            total_pieces=self._piece_counter.total_pieces,
            last_stable_weight=self._piece_counter.last_stable_weight,
            baseline_weight=self._piece_counter.baseline_weight,
            piece_weights=list(self._piece_counter.piece_weights),
            decimal_places=self._piece_counter.decimal_places,
        )

    def force_calibrate(self, stable_weight: float, pieces: int) -> bool:
        """Force recalibration. Returns True if applied."""
        old_count = self._piece_counter.total_pieces
        if not self._piece_counter.force_calibrate(stable_weight, pieces):
            return False
        self._mark_target_edge_if_crossed(
            old_count, self._piece_counter.total_pieces, self._piece_counter.state
        )
        return True

    def reset(self) -> None:
        self._piece_counter.reset()
        self._abnormal_edge = False
        self._target_edge = False

    def consume_abnormal_edge(self) -> bool:
        result = self._abnormal_edge
        self._abnormal_edge = False
        return result

    def consume_target_edge(self) -> bool:
        result = self._target_edge
        self._target_edge = False
        return result

    def current_result(self) -> CountResult:
        return self._build_result()
