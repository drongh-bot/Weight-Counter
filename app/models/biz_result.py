# app/models/biz_result.py

from dataclasses import dataclass
from enum import Enum


class BizState(Enum):
    ZERO = 0
    NORMAL = 1
    ABNORMAL = 2


@dataclass
class BizResult:
    added: bool
    abnormal_high: bool
    abnormal_low: bool
    state: BizState
    delta: float
    avg_weight: float
    tol_high: float
    tol_low: float
    total_pieces: int
    last_stable_weight: float
    last_base_weight: float
    weights: list[float]
    decimal_places: int = 2
