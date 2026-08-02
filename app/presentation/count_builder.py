# app/presentation/count_builder.py
from app.models.count_result import CountResult
from app.models.counter_state import CounterState
from app.presentation.styles import Styles
from app.presentation.view_models import CountSnapshot, LabelItem


class CountBuilder:
    @staticmethod
    def build(result: CountResult) -> CountSnapshot:
        dp = result.decimal_places
        if result.state == CounterState.ZERO:
            state_text = "等待第一件"
            state_style = ""
        elif result.state == CounterState.NORMAL:
            state_text = "正常"
            state_style = ""
        else:
            state_text = "异常（偏高）" if result.abnormal_high else "异常（偏低）"
            state_style = (
                Styles.ABNORMAL_HIGH if result.abnormal_high else Styles.ABNORMAL_LOW
            )

        delta_style = state_style if result.state == CounterState.ABNORMAL else ""

        return CountSnapshot(
            delta_weight=LabelItem(
                text=f"{result.delta:.{dp}f}",
                style=delta_style,
            ),
            state=LabelItem(
                text=state_text,
                style=state_style,
            ),
            avg_weight=f"{result.avg_weight:.{dp}f}",
            tolerance_high=f"{result.tolerance_high:.{dp}f}",
            tolerance_low=f"{result.tolerance_low:.{dp}f}",
            total_pieces=str(result.total_pieces),
            last_stable_weight=f"{result.last_stable_weight:.{dp}f}",
            baseline_weight=f"{result.baseline_weight:.{dp}f}",
            piece_weights=list(result.piece_weights),
            decimal_places=dp,
        )
