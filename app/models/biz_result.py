# app/models/biz_result.py

from dataclasses import dataclass

from app.models.counter_state import CounterState


@dataclass
class BizResult:
    added: bool
    abnormal_high: bool
    abnormal_low: bool
    state: CounterState
    delta: float
    avg_weight: float
    tol_high: float
    tol_low: float
    total_pieces: int
    last_stable_weight: float
    last_base_weight: float
    weights: list[float]
    decimal_places: int = 2
