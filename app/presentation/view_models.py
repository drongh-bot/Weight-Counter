# app/presentation/view_models.py
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
    start_enabled: bool = True
    stop_enabled: bool = True
    force_enabled: bool = False
    start_params_enabled: bool = True


@dataclass
class CountSnapshot:
    delta_weight: LabelItem
    state: LabelItem
    avg_weight: str
    tolerance_high: str
    tolerance_low: str
    total_pieces: str
    last_stable_weight: str
    baseline_weight: str
    piece_weights: list[float]
    decimal_places: int
