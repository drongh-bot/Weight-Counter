# app/presentation/count_display.py
"""计件区展示用纯函数（无 Qt），供 MainWindow 与单测使用。"""

from app.models.count_snapshot import CountSnapshot
from app.models.counter_state import CounterState
from app.models.formatting import format_weight
from app.presentation.view_data import CountDisplay, LabelItem, Styles


def build_count_display(snap: CountSnapshot) -> CountDisplay:
    """CountSnapshot → 计件区展示数据；所有格式化与样式规则集中于此。"""
    if snap.state == CounterState.ZERO:
        state_text, state_style = "等待第一件", ""
    elif snap.state == CounterState.NORMAL:
        state_text, state_style = "正常", ""
    elif snap.abnormal_high:
        state_text, state_style = "异常（偏高）", Styles.ABNORMAL_HIGH
    else:
        state_text, state_style = "异常（偏低）", Styles.ABNORMAL_LOW

    def weight_text(value: float) -> str:
        return format_weight(value, snap.decimal_places)

    return CountDisplay(
        # state_style 在 ZERO/NORMAL 时是空串，恰好符合「Δ 不着色」的规则
        delta=LabelItem(text=weight_text(snap.delta_weight), style=state_style),
        state=LabelItem(text=state_text, style=state_style),
        avg_text=weight_text(snap.avg_weight),
        tol_high_text=weight_text(snap.tolerance_high),
        tol_low_text=weight_text(snap.tolerance_low),
        total_text=str(snap.total_pieces),
        last_stable_text=weight_text(snap.last_stable_weight),
        baseline_text=weight_text(snap.baseline_weight),
    )
