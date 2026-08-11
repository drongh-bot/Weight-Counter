# app/models/count_snapshot.py

from dataclasses import dataclass

from app.models.counter_state import CounterState


@dataclass
class CountSnapshot:
    """当前件数、均重、公差、是否异常等（给界面显示；不含「这一次刚发生了什么」）。"""

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
    decimal_places: int


@dataclass
class CountFrame(CountSnapshot):
    """一次计件（或强制校准）之后的结果：上面那些数 + 是否刚加件/刚进异常/刚达目标。"""

    piece_added: bool = False
    abnormal_edge: bool = False
    target_edge: bool = False
