# app/models/counter_state.py
from enum import Enum, auto


class CounterState(Enum):
    ZERO = auto()
    NORMAL = auto()
    ABNORMAL = auto()
