# app/services/ui/builders.py
from app.models.count_result import CountResult
from app.models.counter_state import CounterState
from app.services.ui.view_models import BarStatus, CountSnapshot, LabelItem
from app.services.ui.styles import Styles


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
            piece_weights=result.piece_weights,
            decimal_places=dp,
        )


class BarStatusBuilder:
    @staticmethod
    def build(
        parse_ok: bool,
        comm_ok: bool,
        status_message: str | None,
        *,
        info: bool = False,
    ) -> BarStatus:
        if not comm_ok:
            parse_text = "解析等待"
            parse_style = Styles.GRAY
        elif not parse_ok:
            parse_text = "解析异常"
            parse_style = Styles.RED
        else:
            parse_text = "解析正常"
            parse_style = Styles.GREEN

        if status_message:
            msg_style = Styles.GRAY if info else Styles.RED
        else:
            msg_style = ""

        return BarStatus(
            parse=LabelItem(text=parse_text, style=parse_style),
            comm=LabelItem(
                text="通讯正常" if comm_ok else "通讯等待",
                style=Styles.GREEN if comm_ok else Styles.GRAY,
            ),
            message=LabelItem(
                text=status_message or "无异常",
                style=msg_style,
            ),
        )
