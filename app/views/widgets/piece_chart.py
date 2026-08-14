import pyqtgraph as pg
from PySide6.QtCore import QPointF, Qt
from PySide6.QtWidgets import QHBoxLayout, QScrollBar, QVBoxLayout, QWidget


class FixedAxis(pg.AxisItem):
    """固定小数位数的水平轴。"""

    def __init__(self, orientation) -> None:
        super().__init__(orientation=orientation)
        self.decimals = 2

    def tickStrings(self, values, scale, spacing) -> list[str]:
        fmt = f"{{:.{self.decimals}f}}"
        return [fmt.format(v) for v in values]


class PieceChart(QWidget):
    """单件重量散点图，支持悬停与纵向滚动。

    约定：图中 Y 坐标 = 件号（从 1 起），与列表索引差 1。
    """

    _DEFAULT_Y_WINDOW_SIZE: int = 20
    _MAX_Y_TICK_LABELS: int = 20

    def __init__(self, decimal_places: int = 2, parent=None) -> None:
        super().__init__(parent)

        self._piece_weights: list[float] = []
        self._decimal_places: int = decimal_places
        self._hovered_index: int | None = None
        self._follow_latest: bool = True
        self._setting_range: bool = False

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        inner = QHBoxLayout()
        inner.setContentsMargins(0, 0, 0, 0)
        inner.setSpacing(0)

        self._setup_plot()
        inner.addWidget(self.plot, 1)

        self._setup_scrollbar()
        inner.addWidget(self.scrollbar, 0)

        outer.addLayout(inner)

        self._setup_scatter()

        scene = self.plot.scene()
        scene.sigMouseMoved.connect(self._on_mouse_moved)
        self.plot.getViewBox().sigRangeChanged.connect(self._on_range_changed)

    def _setup_plot(self) -> None:
        self.plot = pg.PlotWidget(
            background="w",
            axisItems={
                "bottom": FixedAxis("bottom"),
                "top": FixedAxis("top"),
            },
        )
        self.plot.setAntialiasing(True)

        self.plot.getAxis("bottom").decimals = self._decimal_places
        self.plot.getAxis("top").decimals = self._decimal_places

        self.plot.showGrid(x=True, y=True, alpha=0.3)
        for name in ("left", "bottom", "top"):
            axis = self.plot.getAxis(name)
            axis.setPen("k")
            axis.setTextPen("k")
        self.plot.getAxis("bottom").hide()
        self.plot.getAxis("left").setTicks([])
        self.plot.getPlotItem().setMenuEnabled(False)

        plot_item = self.plot.getPlotItem()
        self.plot.setLabel("top", "重量", color="k", bold=True)
        plot_item.layout.setContentsMargins(30, 14, 2, 2)

    def _setup_scatter(self) -> None:
        self.scatter = pg.ScatterPlotItem(
            size=10,
            brush=pg.mkBrush(0, 0, 255, 180),
            pen=pg.mkPen("w", width=1),
        )
        self.scatter.setZValue(1)
        self.plot.addItem(self.scatter)

        self.hover_point = pg.ScatterPlotItem(
            size=14,
            brush=pg.mkBrush(255, 0, 0, 220),
            pen=pg.mkPen("w", width=2),
        )
        self.hover_point.setZValue(2)
        self.plot.addItem(self.hover_point)

    def _setup_scrollbar(self) -> None:
        self.scrollbar = QScrollBar(Qt.Orientation.Vertical)
        self.scrollbar.setRange(0, 0)
        self.scrollbar.hide()
        self.scrollbar.valueChanged.connect(self._on_scrollbar_moved)

    def update_piece_weights(self, piece_weights: list[float]) -> None:
        """更新件重数据并重绘（不可见时仅缓存；清空时始终清散点）。"""
        if piece_weights == self._piece_weights:
            return

        self._piece_weights = list(piece_weights)

        if not self._piece_weights:
            self.reset()
            return

        if not self.isVisible():
            return

        self._render()

    def reset(self) -> None:
        """清空图表与滚动条。"""
        self._piece_weights = []
        self._hovered_index = None
        self._follow_latest = True
        self.scatter.setData([])
        self.hover_point.setData([])
        self.plot.getAxis("left").setTicks([])
        self.scrollbar.blockSignals(True)
        self.scrollbar.setRange(0, 0)
        self.scrollbar.hide()
        self.scrollbar.blockSignals(False)

    def set_decimal_places(self, places: int) -> None:
        """切换轴标签小数位数。"""
        if places == self._decimal_places:
            return
        self._decimal_places = places
        for name in ("bottom", "top"):
            axis = self.plot.getAxis(name)
            axis.decimals = places
            axis.picture = None  # 清掉轴标签缓存，强制重绘
        if self._piece_weights and self.isVisible():
            self.plot.scene().update()

    def _render(self) -> None:
        """按当前件重列表重绘散点、坐标轴与滚动范围。"""
        count = len(self._piece_weights)
        self._update_scatter_and_ticks(count)

        if count <= self._DEFAULT_Y_WINDOW_SIZE:
            y_min, y_max = 0.0, float(count + 1)
        elif self._follow_latest:
            y_min = float(count - self._DEFAULT_Y_WINDOW_SIZE + 1)
            y_max = float(count + 1)
        else:
            y_min, y_max = self.plot.viewRange()[1]

        self._apply_y_range(y_min, y_max)
        self.scrollbar.setVisible(count > self._DEFAULT_Y_WINDOW_SIZE)
        self._update_x_range(count)

    def _update_scatter_and_ticks(self, count: int) -> None:
        """更新散点数据与左侧序号刻度。"""
        spots = [
            {"pos": (weight, i + 1)} for i, weight in enumerate(self._piece_weights)
        ]
        self.scatter.setData(spots)

        if count <= self._MAX_Y_TICK_LABELS:
            step = 1
        else:
            step = max(count // self._MAX_Y_TICK_LABELS, 1)
        ticks = [(i + 1, str(i + 1)) for i in range(0, count, step)]
        self.plot.getAxis("left").setTicks([ticks])

    def _update_x_range(self, count: int) -> None:
        """按可见件重自动调整 X 轴范围。"""
        vrange = self.plot.viewRange()[1]
        # Y 刻度即件号（= 索引 + 1），把可见的件号范围转成索引切片
        start_idx = max(0, int(vrange[0]) - 1)
        end_idx = min(count, int(vrange[1]) + 1)
        visible = self._piece_weights[start_idx:end_idx]
        if not visible:
            return

        x_min = min(visible)
        x_max = max(visible)
        span = x_max - x_min
        if span < 1e-9:
            margin = max(abs(x_min) * 0.05, 1.0)
        else:
            margin = max(span * 0.1, 0.05)
        self.plot.setXRange(x_min - margin, x_max + margin, padding=0)

    def _on_mouse_moved(self, pos: QPointF) -> None:
        """鼠标移动时高亮最近片号并显示 tip。"""
        if not self._piece_weights:
            return

        view_box = self.plot.getViewBox()
        mouse_point = view_box.mapSceneToView(pos)

        closest_y = int(round(mouse_point.y()))
        index = closest_y - 1

        if not (0 <= index < len(self._piece_weights)):
            if self._hovered_index is not None:
                self.hover_point.setData([])
                self.plot.setToolTip("")
                self._hovered_index = None
            return

        if index == self._hovered_index:
            return

        self._hovered_index = index
        weight = self._piece_weights[index]

        self.hover_point.setData([{"pos": (weight, closest_y)}])
        self.plot.setToolTip(
            f"片号：{closest_y}\n重量：{weight:.{self._decimal_places}f}"
        )

    def _on_scrollbar_moved(self, value: int) -> None:
        """滚动条拖动时同步图表 Y 窗口。"""
        if self._setting_range or not self._piece_weights:
            return

        count = len(self._piece_weights)
        window = self.scrollbar.pageStep() or self._DEFAULT_Y_WINDOW_SIZE
        y_min = float(count - window - value + 1)
        y_max = y_min + float(window)

        self._follow_latest = value == 0
        self._apply_y_range(y_min, y_max)

    def _on_range_changed(self, _viewbox, ranges) -> None:
        if self._setting_range or not self._piece_weights:
            return

        ymin = ranges[1][0]
        ymax = ranges[1][1]
        # 窗口顶贴近最新件（0.5 容忍半件）即视为跟随最新
        self._follow_latest = ymax >= len(self._piece_weights) - 0.5
        self._sync_scrollbar(ymin, ymax)

    def _apply_y_range(self, y_min: float, y_max: float) -> None:
        self._setting_range = True
        self.plot.setYRange(y_min, y_max, padding=0)
        self._sync_scrollbar(y_min, y_max)
        self._setting_range = False

    def _sync_scrollbar(self, y_min: float, y_max: float) -> None:
        # 滚动条值 ↔ Y 窗口下沿：value = 总件数 - 窗高 - y_min + 1
        # （滚动条 0 表示窗口贴最新件，最大值 top 表示窗口下沿到件号 1）
        height = int(y_max - y_min)
        count = len(self._piece_weights)
        value = max(0, count - height - int(y_min) + 1)
        top = max(0, count - height)

        self.scrollbar.blockSignals(True)
        self.scrollbar.setRange(0, top)
        self.scrollbar.setPageStep(height)
        self.scrollbar.setValue(min(value, top))
        self.scrollbar.blockSignals(False)

    def showEvent(self, event) -> None:
        """窗口显示时补绘缓存数据；缓存为空则确保散点已清空。"""
        super().showEvent(event)
        if self._piece_weights:
            self._render()
        else:
            self.scatter.setData([])
            self.hover_point.setData([])
