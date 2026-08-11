# app/presentation/count_labels.py
"""计件区展示用纯函数（无 Qt），供 MainWindow 与单测使用。"""

from app.models.count_snapshot import CountSnapshot
from app.models.counter_state import CounterState
from app.presentation.view_models import LabelItem, Styles


def state_label(snap: CountSnapshot) -> LabelItem:
    """状态枚举 → 文案与样式。"""
    if snap.state == CounterState.ZERO:
        return LabelItem(text="等待第一件", style="")
    if snap.state == CounterState.NORMAL:
        return LabelItem(text="正常", style="")
    if snap.abnormal_high:
        return LabelItem(text="异常（偏高）", style=Styles.ABNORMAL_HIGH)
    return LabelItem(text="异常（偏低）", style=Styles.ABNORMAL_LOW)


def delta_style(snap: CountSnapshot) -> str:
    """Δ 重量在异常态时跟状态同色，否则无样式。"""
    if snap.state != CounterState.ABNORMAL:
        return ""
    return Styles.ABNORMAL_HIGH if snap.abnormal_high else Styles.ABNORMAL_LOW
