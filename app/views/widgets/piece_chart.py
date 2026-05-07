import pyqtgraph as pg
from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QVBoxLayout, QWidget


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
    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.data_list: list[float] = []
        self._decimal_places: int = 2

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Use custom bottom axis
        self.plot = pg.PlotWidget(
            background="w",
            axisItems={
                "bottom": FixedAxis("bottom"),
                "top": FixedAxis("top"),
            },
        )

        self.plot.setAntialiasing(True)

        self.plot.showGrid(x=True, y=True, alpha=0.3)
        self.plot.getAxis("left").setPen("k")
        self.plot.getAxis("bottom").setPen("k")
        self.plot.getAxis("left").setTicks([])
        self.plot.getPlotItem().setMenuEnabled(False)
        layout.addWidget(self.plot)

        plot_item = self.plot.getPlotItem()

        # Top axis label
        self.plot.setLabel("top", "重量")

        plot_item.layout.setContentsMargins(30, 15, 2, 2)

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

        # Hover binding
        scene = self.plot.scene()
        scene.sigMouseMoved.connect(self.on_mouse_moved)

    def _reset(self) -> None:
        self.data_list = []
        self.scatter.setData([])
        self.hover_point.setData([])
        self.plot.getAxis("left").setTicks([])

    def update_chart(self, new_list: list[float], decimal_places: int = 2) -> None:
        self.data_list = list(new_list)
        self._decimal_places = decimal_places

        if not self.isVisible():
            return

        count = len(self.data_list)
        if count == 0:
            self._reset()
            return

        # Scatter: newest on top
        spots = [{"pos": (weight, i + 1)} for i, weight in enumerate(self.data_list)]
        self.scatter.setData(spots)

        # Y-axis index
        ticks = [(i + 1, str(i + 1)) for i in range(count)]
        self.plot.getAxis("left").setTicks([ticks])

        # Auto range
        self.plot.autoRange()

        # Sync axis decimal places
        self.plot.getAxis("bottom").decimals = decimal_places
        self.plot.getAxis("top").decimals = decimal_places

    def on_mouse_moved(self, pos: QPointF) -> None:
        if not self.data_list:
            return

        view_box = self.plot.getViewBox()
        mouse_point = view_box.mapSceneToView(pos)

        closest_y = int(round(mouse_point.y()))
        index = closest_y - 1

        if not (0 <= index < len(self.data_list)):
            self.hover_point.setData([])
            self.plot.setToolTip("")
            return

        weight = self.data_list[index]

        self.hover_point.setData([{"pos": (weight, closest_y)}])

        self.plot.setToolTip(f"片号：{closest_y}\n重量：{weight:.{self._decimal_places}f}")

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if self.data_list:
            self.update_chart(self.data_list, self._decimal_places)
