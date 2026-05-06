# app/services/ui/models.py
from dataclasses import dataclass


@dataclass
class LabelItem:
    """Generic label item: text + style."""
    text: str
    style: str


@dataclass
class StatusData:
    parse: LabelItem
    comm: LabelItem
    exception: LabelItem


@dataclass
class BizData:
    delta_weight: LabelItem
    state: LabelItem
    avg_weight: str
    tol_high: str
    tol_low: str
    total_pieces: str
    last_stable_weight: str
    last_base_weight: str
    weights: list[float]


@dataclass
class ButtonState:
    start: bool = True
    stop: bool = True
    clear: bool = False
    force: bool = False


@dataclass
class UIData:
    button_state: ButtonState
    actual_weight: str
    status: StatusData
    biz: BizData
