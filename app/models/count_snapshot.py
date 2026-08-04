# app/models/count_snapshot.py

from dataclasses import dataclass

from app.models.counter_state import CounterState


@dataclass
class CountSnapshot:
    """当前计件状态快照（无边沿）。"""

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


@dataclass
class CountFrame(CountSnapshot):
    """本帧计件结果：快照 + 边沿（仅 process / force_calibrate 产生）。"""

    piece_added: bool = False
    abnormal_edge: bool = False
    target_edge: bool = False
