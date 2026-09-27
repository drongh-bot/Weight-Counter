# app/presentation/view_data.py
from dataclasses import dataclass


class Styles:
    """状态栏与计件标签的 Qt 样式表常量。"""

    GREEN = "color: green;"
    GRAY = "color: gray;"
    RED = "color: red;"
    ABNORMAL_HIGH = "color: white; background-color: red;"
    ABNORMAL_LOW = "color: white; background-color: blue;"


@dataclass
class StyledText:
    """要贴到 QLabel 上的一对值：显示什么字、配什么样式。"""

    text: str
    style: str


@dataclass
class BarSnapshot:
    """状态栏三格（解析 / 通讯 / 消息）的一帧快照。"""

    parse: StyledText
    comm: StyledText
    message: StyledText


@dataclass
class ControlStatus:
    """Start / Stop / 强制校准 / Spinbox 等控件的可用状态。"""

    start_enabled: bool = True
    stop_enabled: bool = False
    force_enabled: bool = False
    start_params_enabled: bool = True


@dataclass(frozen=True)
class CountDisplay:
    """计件区一帧的完整展示数据：文本全部格式化好，视图只负责贴。"""

    delta: StyledText  # Δ值 + 样式（异常时着色）
    state: StyledText  # 状态文案 + 样式
    avg_text: str
    tol_high_text: str
    tol_low_text: str
    total_text: str
    last_stable_text: str
    baseline_text: str
