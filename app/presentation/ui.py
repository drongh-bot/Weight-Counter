# app/presentation/ui.py
from PySide6.QtCore import QObject, Signal

from app.models.count_snapshot import CountSnapshot
from app.presentation.count_builder import to_count_view
from app.presentation.view_models import BarSnapshot, ButtonStatus, CountView


class UiBridge(QObject):
    """控制器 ↔ 主窗口的信号中转（不是 Qt Designer 的 Ui_MainWindow）。

    Controller 只调用本类的 update_*；MainWindow 只连接下面的 Signal 做绘制。
    各 update_* 会与上次内容比较，相同则不 emit，避免串口高频帧刷爆 UI。
    """

    count_changed = Signal(CountView)
    bar_snapshot_changed = Signal(BarSnapshot)
    button_status_changed = Signal(ButtonStatus)
    actual_weight_changed = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        # 上次已发出的内容，用于去重
        self._last_count: CountView | None = None
        self._last_bar: BarSnapshot | None = None
        self._last_button: ButtonStatus | None = None
        self._last_weight: str | None = None

    def update_count(self, snap: CountSnapshot) -> None:
        """把计件快照转成展示数据，有变化时通知窗口刷新件数/公差等标签。"""
        count_view = to_count_view(snap)
        if count_view != self._last_count:
            self._last_count = count_view
            self.count_changed.emit(count_view)

    def update_bar(self, snapshot: BarSnapshot) -> None:
        """推送状态栏三格（解析 / 通讯 / 消息）的完整一帧快照。"""
        if snapshot != self._last_bar:
            self._last_bar = snapshot
            self.bar_snapshot_changed.emit(snapshot)

    def update_button_status(self, state: ButtonStatus) -> None:
        """同步 Start / Stop / 强制校准等按钮的可用状态。"""
        if state != self._last_button:
            self._last_button = state
            self.button_status_changed.emit(state)

    def update_actual_weight(self, weight: float | None, decimal_places: int) -> None:
        """刷新「当前秤重」显示；weight 为 None 时显示占位符 -----。"""
        text = f"{weight:.{decimal_places}f}" if weight is not None else "-----"
        if text != self._last_weight:
            self._last_weight = text
            self.actual_weight_changed.emit(text)

    def refresh(self) -> None:
        """强制重发上次缓存的全部信号（例如窗口重建后需要重绘，不依赖数据是否变化）。"""
        if self._last_count:
            self.count_changed.emit(self._last_count)
        if self._last_bar:
            self.bar_snapshot_changed.emit(self._last_bar)
        if self._last_button:
            self.button_status_changed.emit(self._last_button)
        if self._last_weight is not None:
            self.actual_weight_changed.emit(self._last_weight)
