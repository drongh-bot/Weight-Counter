# app/presentation/ui_bridge.py
from dataclasses import fields

from PySide6.QtCore import QObject, Signal

from app.models.count_snapshot import CountSnapshot
from app.presentation.view_models import BarSnapshot, ButtonStatus


class UiBridge(QObject):
    """控制器和主窗口之间的传话筒。

    控制器只调用 update_* 说「数据变了」；主窗口只监听信号来改标签、表格、图。
    内容没变就不通知，避免秤数据太密时界面一直闪。
    """

    count_changed = Signal(CountSnapshot)
    bar_snapshot_changed = Signal(BarSnapshot)
    button_status_changed = Signal(ButtonStatus)
    actual_weight_changed = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._last_count: CountSnapshot | None = None
        self._last_bar: BarSnapshot | None = None
        self._last_button: ButtonStatus | None = None
        self._last_weight: str | None = None

    @staticmethod
    def _display_snapshot(snap: CountSnapshot) -> CountSnapshot:
        """只留下界面要显示的那些数，方便判断「画面有没有真的变」。"""
        return CountSnapshot(
            **{f.name: getattr(snap, f.name) for f in fields(CountSnapshot)}
        )

    def update_count(self, snap: CountSnapshot) -> None:
        """件数、均重、公差等变了就通知主窗口刷新计件区。"""
        display = self._display_snapshot(snap)
        if display != self._last_count:
            self._last_count = display
            self.count_changed.emit(display)

    def update_bar(self, snapshot: BarSnapshot) -> None:
        """底部「解析 / 通讯 / 消息」三格有变化就通知主窗口。"""
        if snapshot != self._last_bar:
            self._last_bar = snapshot
            self.bar_snapshot_changed.emit(snapshot)

    def update_button_status(self, state: ButtonStatus) -> None:
        """Start / Stop / 强制校准等按钮能不能点。"""
        if state != self._last_button:
            self._last_button = state
            self.button_status_changed.emit(state)

    def update_actual_weight(self, weight: float | None, decimal_places: int) -> None:
        """刷新「当前秤重」；没有有效重量时显示 -----。"""
        text = f"{weight:.{decimal_places}f}" if weight is not None else "-----"
        if text != self._last_weight:
            self._last_weight = text
            self.actual_weight_changed.emit(text)

    def refresh(self) -> None:
        """把上次的内容再推一遍（例如窗口重开后要立刻画出来）。"""
        if self._last_count:
            self.count_changed.emit(self._last_count)
        if self._last_bar:
            self.bar_snapshot_changed.emit(self._last_bar)
        if self._last_button:
            self.button_status_changed.emit(self._last_button)
        if self._last_weight is not None:
            self.actual_weight_changed.emit(self._last_weight)
