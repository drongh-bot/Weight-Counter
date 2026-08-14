# app/presentation/count_labels.py
"""计件区展示用纯函数（无 Qt），供 MainWindow 与单测使用。"""

from app.models.count_snapshot import CountSnapshot
from app.models.counter_state import CounterState
from app.presentation.view_models import CountDisplay, Styles


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
        dp = snap.decimal_places
        return f"{value:.{dp}f}"

    return CountDisplay(
        delta_text=weight_text(snap.delta),
        delta_style=state_style,  # ZERO/NORMAL 时 state_style 为空，恰好符合「Δ 无样式」的规则
        state_text=state_text,
        state_style=state_style,
        avg_text=weight_text(snap.avg_weight),
        tol_high_text=weight_text(snap.tolerance_high),
        tol_low_text=weight_text(snap.tolerance_low),
        total_text=str(snap.total_pieces),
        last_stable_text=weight_text(snap.last_stable_weight),
        baseline_text=weight_text(snap.baseline_weight),
        piece_weights=snap.piece_weights,
    )
