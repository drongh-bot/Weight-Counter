# app/models/counter_state.py
from enum import Enum, auto


class CounterState(Enum):
    """计件 FSM 三态。"""

    ZERO = auto()
    NORMAL = auto()
    ABNORMAL = auto()
