# app/services/ui/builders.py
from app.models.biz_result import BizResult, BizState
from app.services.ui.models import BizData, LabelItem, StatusData
from app.services.ui.styles import Styles


class BizBuilder:
    @staticmethod
    def build(biz: BizResult) -> BizData:
        if biz.state == BizState.ZERO:
            state_text = "等待第一件"
            state_style = ""
        elif biz.state == BizState.NORMAL:
            state_text = "正常"
            state_style = ""
        else:
            state_text = "异常（偏高）" if biz.abnormal_high else "异常（偏低）"
            state_style = Styles.ABN_HI if biz.abnormal_high else Styles.ABN_LO

        delta_style = state_style if biz.state == BizState.ABNORMAL else ""

        return BizData(
            delta_weight=LabelItem(
                text=f"{biz.delta:.3f}",
                style=delta_style,
            ),
            state=LabelItem(
                text=state_text,
                style=state_style,
            ),
            avg_weight=f"{biz.avg_weight:.3f}",
            tol_high=f"{biz.tol_high:.3f}",
            tol_low=f"{biz.tol_low:.3f}",
            total_pieces=str(biz.total_pieces),
            last_stable_weight=f"{biz.last_stable_weight:.3f}",
            last_base_weight=f"{biz.last_base_weight:.3f}",
            weights=biz.weights,
        )


class StatusBuilder:
    @staticmethod
    def build(parse_ok: bool, comm_ok: bool, exception_text: str | None) -> StatusData:
        return StatusData(
            parse=LabelItem(
                text="解析正常" if parse_ok else "解析等待",
                style=Styles.GREEN if parse_ok else Styles.GRAY,
            ),
            comm=LabelItem(
                text="通讯正常" if comm_ok else "通讯等待",
                style=Styles.GREEN if comm_ok else Styles.GRAY,
            ),
            exception=LabelItem(
                text=exception_text or "无异常",
                style=Styles.RED if exception_text else "",
            ),
        )
