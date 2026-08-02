# app/presentation/ui.py
from PySide6.QtCore import QObject, Signal

from app.models.count_result import CountResult
from app.presentation.builders import CountBuilder, BarStatusBuilder
from app.presentation.view_models import CountSnapshot, ButtonStatus, BarStatus


class Ui(QObject):
    count_changed = Signal(CountSnapshot)
    bar_status_changed = Signal(BarStatus)
    button_status_changed = Signal(ButtonStatus)
    actual_weight_changed = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._last_count: CountSnapshot | None = None
        self._last_bar: BarStatus | None = None
        self._last_button: ButtonStatus | None = None
        self._last_weight: str | None = None

    def update_count(self, result: CountResult) -> None:
        data = CountBuilder.build(result)
        if data != self._last_count:
            self._last_count = data
            self.count_changed.emit(data)

    def update_bar_status(
        self,
        parse_ok: bool = True,
        comm_ok: bool = True,
        status_message: str | None = None,
        *,
        info: bool = False,
    ) -> None:
        data = BarStatusBuilder.build(
            parse_ok, comm_ok, status_message, info=info
        )
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
        if self._last_count:
            self.count_changed.emit(self._last_count)
        if self._last_bar:
            self.bar_status_changed.emit(self._last_bar)
        if self._last_button:
            self.button_status_changed.emit(self._last_button)
        if self._last_weight is not None:
            self.actual_weight_changed.emit(self._last_weight)
