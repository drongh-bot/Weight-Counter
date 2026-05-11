# app/services/ui/ui_service.py
from PySide6.QtCore import QObject, Signal

from app.models.biz_result import BizResult
from app.services.ui.builders import BizBuilder, BarStatusBuilder
from app.services.ui.models import BizSnapshot, ButtonStatus, BarStatus


class UIService(QObject):
    biz_changed = Signal(BizSnapshot)
    bar_status_changed = Signal(BarStatus)
    button_status_changed = Signal(ButtonStatus)
    actual_weight_changed = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._last_biz: BizSnapshot | None = None
        self._last_bar: BarStatus | None = None
        self._last_button: ButtonStatus | None = None
        self._last_weight: str | None = None

    def update_biz(self, biz: BizResult) -> None:
        data = BizBuilder.build(biz)
        if data != self._last_biz:
            self._last_biz = data
            self.biz_changed.emit(data)

    def update_bar_status(
        self,
        parse_ok: bool = True,
        comm_ok: bool = True,
        exception_text: str | None = None,
    ) -> None:
        data = BarStatusBuilder.build(parse_ok, comm_ok, exception_text)
        if data != self._last_bar:
            self._last_bar = data
            self.bar_status_changed.emit(data)

    def update_button_status(self, state: ButtonStatus) -> None:
        if state != self._last_button:
            self._last_button = state
            self.button_status_changed.emit(state)

    def update_actual_weight(self, weight: float | None, decimal_places: int) -> None:
        text = f"{weight:.{decimal_places}f}" if weight is not None else "-----"
        if text != self._last_weight:
            self._last_weight = text
            self.actual_weight_changed.emit(text)

    def refresh(self) -> None:
        if self._last_biz:
            self.biz_changed.emit(self._last_biz)
        if self._last_bar:
            self.bar_status_changed.emit(self._last_bar)
        if self._last_button:
            self.button_status_changed.emit(self._last_button)
        if self._last_weight is not None:
            self.actual_weight_changed.emit(self._last_weight)
