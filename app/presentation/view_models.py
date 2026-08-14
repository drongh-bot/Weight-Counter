# app/presentation/view_models.py
from dataclasses import dataclass


class Styles:
    """状态栏与计件标签的 Qt 样式表常量。"""

    GREEN = "color: green;"
    GRAY = "color: gray;"
    RED = "color: red;"
    ABNORMAL_HIGH = "color: white; background-color: red;"
    ABNORMAL_LOW = "color: white; background-color: blue;"


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


@dataclass
class ButtonStatus:
    """Start / Stop / 强制校准等按钮的可用状态。"""

    start_enabled: bool = True
    stop_enabled: bool = False
    force_enabled: bool = False
    start_params_enabled: bool = True


@dataclass(frozen=True)
class CountDisplay:
    """计件区一帧的完整展示数据：文本全部格式化好，视图只负责贴。"""

    delta_text: str
    delta_style: str
    state_text: str
    state_style: str
    avg_text: str
    tol_high_text: str
    tol_low_text: str
    total_text: str
    last_stable_text: str
    baseline_text: str
    piece_weights: list[float]
