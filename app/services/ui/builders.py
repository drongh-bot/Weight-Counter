# app/services/ui/builders.py
from app.models.biz_result import BizResult
from app.models.counter_state import CounterState
from app.services.ui.models import BarStatus, BizSnapshot, LabelItem
from app.services.ui.styles import Styles


class BizBuilder:
    @staticmethod
    def build(biz: BizResult) -> BizSnapshot:
        dp = biz.decimal_places
        if biz.state == CounterState.ZERO:
            state_text = "等待第一件"
            state_style = ""
        elif biz.state == CounterState.NORMAL:
            state_text = "正常"
            state_style = ""
        else:
            state_text = "异常（偏高）" if biz.abnormal_high else "异常（偏低）"
            state_style = Styles.ABNORMAL_HIGH if biz.abnormal_high else Styles.ABNORMAL_LOW

        delta_style = state_style if biz.state == CounterState.ABNORMAL else ""

        return BizSnapshot(
            delta_weight=LabelItem(
                text=f"{biz.delta:.{dp}f}",
                style=delta_style,
            ),
            state=LabelItem(
                text=state_text,
                style=state_style,
            ),
            avg_weight=f"{biz.avg_weight:.{dp}f}",
            tol_high=f"{biz.tol_high:.{dp}f}",
            tol_low=f"{biz.tol_low:.{dp}f}",
            total_pieces=str(biz.total_pieces),
            last_stable_weight=f"{biz.last_stable_weight:.{dp}f}",
            last_base_weight=f"{biz.last_base_weight:.{dp}f}",
            weights=biz.weights,
            decimal_places=dp,
        )


class BarStatusBuilder:
    @staticmethod
    def build(parse_ok: bool, comm_ok: bool, exception_text: str | None) -> BarStatus:
        if not comm_ok:
            parse_text = "解析等待"
            parse_style = Styles.GRAY
        elif not parse_ok:
            parse_text = "解析异常"
            parse_style = Styles.RED
        else:
            parse_text = "解析正常"
            parse_style = Styles.GREEN

        return BarStatus(
            parse=LabelItem(text=parse_text, style=parse_style),
            comm=LabelItem(
                text="通讯正常" if comm_ok else "通讯等待",
                style=Styles.GREEN if comm_ok else Styles.GRAY,
            ),
            exception=LabelItem(
                text=exception_text or "无异常",
                style=Styles.RED if exception_text else "",
            ),
        )
