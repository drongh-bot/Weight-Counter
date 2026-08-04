# app/presentation/view_models.py
from dataclasses import dataclass
from enum import Enum, auto


@dataclass
class LabelItem:
    """通用标签项：文本 + 样式。"""

    text: str
    style: str


@dataclass
class BarSnapshot:
    """状态栏三格（解析 / 通讯 / 消息）的一帧快照。"""

    parse: LabelItem
    comm: LabelItem
    message: LabelItem


class ForceCalibrateResult(Enum):
    """当帧强制校准结果（不锁存；供状态栏选文案）。"""

    NONE = auto()
    DONE = auto()
    FAIL = auto()


@dataclass
class ButtonStatus:
    """Start / Stop / 强制校准等按钮的可用状态。"""

    start_enabled: bool = True
    stop_enabled: bool = True
    force_enabled: bool = False
    start_params_enabled: bool = True


@dataclass
class CountSnapshot:
    """计件区 UI 展示快照。"""

    delta_weight: LabelItem
    state: LabelItem
    avg_weight: str
    tolerance_high: str
    tolerance_low: str
    total_pieces: str
    last_stable_weight: str
    baseline_weight: str
    piece_weights: list[float]
