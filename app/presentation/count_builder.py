# app/presentation/count_builder.py
from app.models.count_snapshot import CountSnapshot
from app.models.counter_state import CounterState
from app.presentation.styles import Styles
from app.presentation.view_models import CountView, LabelItem


def to_count_snapshot(snap: CountSnapshot) -> CountView:
    """领域 CountSnapshot → 展示用 CountView（纯函数，无 Qt）。"""
    dp = snap.decimal_places
    if snap.state == CounterState.ZERO:
        state_text = "等待第一件"
        state_style = ""
    elif snap.state == CounterState.NORMAL:
        state_text = "正常"
        state_style = ""
    else:
        state_text = "异常（偏高）" if snap.abnormal_high else "异常（偏低）"
        state_style = (
            Styles.ABNORMAL_HIGH if snap.abnormal_high else Styles.ABNORMAL_LOW
        )

    delta_style = state_style if snap.state == CounterState.ABNORMAL else ""

    return CountView(
        delta_weight=LabelItem(
            text=f"{snap.delta:.{dp}f}",
            style=delta_style,
        ),
        state=LabelItem(
            text=state_text,
            style=state_style,
        ),
        avg_weight=f"{snap.avg_weight:.{dp}f}",
        tolerance_high=f"{snap.tolerance_high:.{dp}f}",
        tolerance_low=f"{snap.tolerance_low:.{dp}f}",
        total_pieces=str(snap.total_pieces),
        last_stable_weight=f"{snap.last_stable_weight:.{dp}f}",
        baseline_weight=f"{snap.baseline_weight:.{dp}f}",
        piece_weights=list(snap.piece_weights),
    )
