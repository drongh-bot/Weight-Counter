# app/presentation/ui_bridge.py
from dataclasses import fields

from PySide6.QtCore import QObject, Signal

from app.models.count_snapshot import CountSnapshot
from app.models.formatting import format_weight
from app.presentation.view_data import BarSnapshot, ButtonStatus


class UiBridge(QObject):
    """控制器和主窗口之间的传话筒。

    控制器只调用 update_* 说「数据变了」；主窗口只监听信号来改标签、表格、图。
    内容没变就不通知，避免秤数据太密时界面一直闪。
    """

    count_snapshot_changed = Signal(CountSnapshot)
    bar_snapshot_changed = Signal(BarSnapshot)
    button_status_changed = Signal(ButtonStatus)
    actual_weight_text_changed = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._last_count: CountSnapshot | None = None
        self._last_bar: BarSnapshot | None = None
        self._last_button: ButtonStatus | None = None
        self._last_weight: str | None = None

    @staticmethod
    def _without_edges(snap: CountSnapshot) -> CountSnapshot:
        """丢掉三个边沿（piece_added / abnormal_edge / target_edge），只留展示字段。

        边沿每帧都可能翻，留着会让去重永远判定「变了」；展示字段本身一个不少。
        """
        return CountSnapshot(
            **{f.name: getattr(snap, f.name) for f in fields(CountSnapshot)}
        )

    def update_count_panel(self, snap: CountSnapshot) -> None:
        """件数、均重、公差等变了就通知主窗口刷新计件区。"""
        display = self._without_edges(snap)
        if display != self._last_count:
            self._last_count = display
            self.count_snapshot_changed.emit(display)

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
        text = format_weight(weight, decimal_places) if weight is not None else "-----"
        if text != self._last_weight:
            self._last_weight = text
            self.actual_weight_text_changed.emit(text)
