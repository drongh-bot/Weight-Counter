# app/models/count_result.py

from dataclasses import dataclass

from app.models.counter_state import CounterState


@dataclass
class CountResult:
    """计件结果快照 — CounterService 统一数据载体。"""

    added: bool
    abnormal_high: bool
    abnormal_low: bool
    state: CounterState
    delta: float
    avg_weight: float
    tolerance_high: float
    tolerance_low: float
    total_pieces: int
    last_stable_weight: float
    baseline_weight: float
    piece_weights: list[float]
    decimal_places: int = 2
