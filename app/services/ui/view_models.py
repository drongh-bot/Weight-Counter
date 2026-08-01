# app/services/ui/view_models.py
from dataclasses import dataclass


@dataclass
class LabelItem:
    """Generic label item: text + style."""

    text: str
    style: str


@dataclass
class BarStatus:
    parse: LabelItem
    comm: LabelItem
    message: LabelItem


@dataclass
class ButtonStatus:
    start: bool = True
    stop: bool = True
    clear: bool = False
    force: bool = False


@dataclass
class CountSnapshot:
    delta_weight: LabelItem
    state: LabelItem
    avg_weight: str
    tol_high: str
    tol_low: str
    total_pieces: str
    last_stable_weight: str
    last_base_weight: str
    weights: list[float]
    decimal_places: int
