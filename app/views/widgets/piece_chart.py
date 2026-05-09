import pyqtgraph as pg
from PySide6.QtCore import QPointF, Qt
from PySide6.QtWidgets import QHBoxLayout, QScrollBar, QVBoxLayout, QWidget


# ============================
#   Custom horizontal axis: fixed decimal places
# ============================
class FixedAxis(pg.AxisItem):
    def __init__(self, orientation) -> None:
        super().__init__(orientation=orientation)
        self.decimals = 2

    def tickStrings(self, values, scale, spacing) -> list[str]:
        fmt = f"{{:.{self.decimals}f}}"
        return [fmt.format(v) for v in values]


class PieceChart(QWidget):
    _WINDOW: int = 20

    def __init__(self, decimal_places: int = 2, parent=None) -> None:
        super().__init__(parent)

        self.data_list: list[float] = []
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

        # Plot
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

        inner.addWidget(self.plot, 1)

        # Scrollbar
        self.scrollbar = QScrollBar(Qt.Orientation.Vertical)
        self.scrollbar.setRange(0, 0)
        self.scrollbar.hide()
        self.scrollbar.valueChanged.connect(self._on_scrollbar_moved)
        inner.addWidget(self.scrollbar, 0)

        outer.addLayout(inner)

        plot_item = self.plot.getPlotItem()
        self.plot.setLabel("top", "重量", color="k", bold=True)
        plot_item.layout.setContentsMargins(30, 14, 2, 2)

        # Scatter
        self.scatter = pg.ScatterPlotItem(
            size=10,
            brush=pg.mkBrush(0, 0, 255, 180),
            pen=pg.mkPen("w", width=1),
        )
        self.scatter.setZValue(1)
        self.plot.addItem(self.scatter)

        # Hover highlight point
        self.hover_point = pg.ScatterPlotItem(
            size=14,
            brush=pg.mkBrush(255, 0, 0, 220),
            pen=pg.mkPen("w", width=2),
        )
        self.hover_point.setZValue(2)
        self.plot.addItem(self.hover_point)

        scene = self.plot.scene()
        scene.sigMouseMoved.connect(self.on_mouse_moved)

        self.plot.getViewBox().sigRangeChanged.connect(self._on_range_changed)

    # ---------------------------------------------------------
    #  Public API
    # ---------------------------------------------------------
    def update_chart(self, new_list: list[float]) -> None:
        self.data_list = list(new_list)

        if not self.isVisible():
            return

        count = len(self.data_list)
        if count == 0:
            self._reset()
            return

        # Scatter
        spots = [{"pos": (weight, i + 1)} for i, weight in enumerate(self.data_list)]
        self.scatter.setData(spots)

        # Y-axis ticks — thin labels when too many
        max_labels = 20
        if count <= max_labels:
            ticks = [(i + 1, str(i + 1)) for i in range(count)]
        else:
            step = max(count // max_labels, 1)
            ticks = [(i + 1, str(i + 1)) for i in range(0, count, step)]
        self.plot.getAxis("left").setTicks([ticks])

        # Y range
        window = self._WINDOW
        if count <= window:
            y_min, y_max = 0.0, float(count + 1)
        elif self._follow_latest:
            y_min = float(count - window + 1)
            y_max = float(count + 1)
        else:
            y_min, y_max = self.plot.viewRange()[1]

        self._apply_y_range(y_min, y_max)

        self.scrollbar.setVisible(count > window)

        # X range
        vrange = self.plot.viewRange()[1]
        start_idx = max(0, int(vrange[0]) - 1)
        end_idx = min(count, int(vrange[1]) + 1)
        visible = self.data_list[start_idx:end_idx]
        if visible:
            x_min = min(visible)
            x_max = max(visible)
            span = x_max - x_min
            if span < 1e-9:
                margin = max(abs(x_min) * 0.05, 1.0)
            else:
                margin = max(span * 0.1, 0.05)
            self.plot.setXRange(x_min - margin, x_max + margin, padding=0)

    def set_decimal_places(self, places: int) -> None:
        if places == self._decimal_places:
            return
        self._decimal_places = places
        for name in ("bottom", "top"):
            axis = self.plot.getAxis(name)
            axis.decimals = places
            axis.picture = None
        if self.data_list and self.isVisible():
            self.plot.scene().update()

    # ---------------------------------------------------------
    #  Hover
    # ---------------------------------------------------------
    def on_mouse_moved(self, pos: QPointF) -> None:
        if not self.data_list:
            return

        view_box = self.plot.getViewBox()
        mouse_point = view_box.mapSceneToView(pos)

        closest_y = int(round(mouse_point.y()))
        index = closest_y - 1

        if not (0 <= index < len(self.data_list)):
            if self._hovered_index is not None:
                self.hover_point.setData([])
                self.plot.setToolTip("")
                self._hovered_index = None
            return

        if index == self._hovered_index:
            return

        self._hovered_index = index
        weight = self.data_list[index]

        self.hover_point.setData([{"pos": (weight, closest_y)}])

        self.plot.setToolTip(
            f"片号：{closest_y}\n重量：{weight:.{self._decimal_places}f}"
        )

    # ---------------------------------------------------------
    #  Scrollbar → chart
    # ---------------------------------------------------------
    def _on_scrollbar_moved(self, value: int) -> None:
        if self._setting_range or not self.data_list:
            return

        count = len(self.data_list)
        window = self.scrollbar.pageStep() or self._WINDOW
        y_min = float(count - window - value + 1)
        y_max = y_min + float(window)

        self._follow_latest = value == 0

        self._apply_y_range(y_min, y_max)

    # ---------------------------------------------------------
    #  Chart drag / wheel zoom → scrollbar
    # ---------------------------------------------------------
    def _on_range_changed(self, _viewbox, ranges) -> None:
        if self._setting_range or not self.data_list:
            return

        ymin = ranges[1][0]
        ymax = ranges[1][1]
        count = len(self.data_list)
        self._follow_latest = ymax >= count - 0.5

        height = int(ymax - ymin)
        value = max(0, count - height - int(ymin) + 1)
        top = max(0, count - height)

        self.scrollbar.blockSignals(True)
        self.scrollbar.setRange(0, top)
        self.scrollbar.setPageStep(height)
        self.scrollbar.setValue(min(value, top))
        self.scrollbar.blockSignals(False)

    # ---------------------------------------------------------
    #  Internal
    # ---------------------------------------------------------
    def _apply_y_range(self, y_min: float, y_max: float) -> None:
        self._setting_range = True
        self.plot.setYRange(y_min, y_max, padding=0)

        if not self.scrollbar.isVisible():
            self._setting_range = False
            return

        height = int(y_max - y_min)
        count = len(self.data_list)
        value = max(0, count - height - int(y_min) + 1)
        top = max(0, count - height)

        self.scrollbar.blockSignals(True)
        self.scrollbar.setRange(0, top)
        self.scrollbar.setPageStep(height)
        self.scrollbar.setValue(min(value, top))
        self.scrollbar.blockSignals(False)

        self._setting_range = False

    def _reset(self) -> None:
        self.data_list = []
        self._hovered_index = None
        self._follow_latest = True
        self.scatter.setData([])
        self.hover_point.setData([])
        self.plot.getAxis("left").setTicks([])
        self.scrollbar.blockSignals(True)
        self.scrollbar.setRange(0, 0)
        self.scrollbar.hide()
        self.scrollbar.blockSignals(False)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if self.data_list:
            self.update_chart(self.data_list)
