# app/services/ui_service.py
from PySide6.QtCore import QObject, Signal

from app.models.biz_result import BizResult
from app.services.ui.builders import BizBuilder, StatusBuilder
from app.services.ui.models import ButtonState, UIData


class UIService(QObject):
    ui_changed = Signal(UIData)

    def __init__(self) -> None:
        super().__init__()
        self._last_ui_data: UIData | None = None

    def update(
        self,
        biz: BizResult,
        button_state: ButtonState,
        actual_weight: float | None = None,
        parse_ok: bool = True,
        comm_ok: bool = True,
        exception_text: str | None = None,
    ) -> None:
        ui_data = UIData(
            button_state=button_state,
            actual_weight=f"{actual_weight:.3f}"
            if actual_weight is not None
            else "-----",
            status=StatusBuilder.build(parse_ok, comm_ok, exception_text),
            biz=BizBuilder.build(biz),
        )

        if ui_data != self._last_ui_data:
            self._last_ui_data = ui_data
            self.ui_changed.emit(ui_data)

    def refresh(self) -> None:
        if self._last_ui_data:
            self.ui_changed.emit(self._last_ui_data)
