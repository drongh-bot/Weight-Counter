from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
)


class PieceTable(QTableWidget):
    """单件重量表格，最新数据在顶部。"""

    _VERTICAL_HEADER_WIDTH = 40
    _MIN_SECTION_WIDTH = 100

    def __init__(self, decimal_places: int = 2, parent=None) -> None:
        super().__init__(parent)

        self._piece_weights: list[float] = []
        self._decimal_places: int = decimal_places
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setColumnCount(1)
        self.setHorizontalHeaderLabels(["重量"])

        vertical_header = self.verticalHeader()
        vertical_header.setFixedWidth(self._VERTICAL_HEADER_WIDTH)
        vertical_header.setDefaultAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )

        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setMinimumSectionSize(self._MIN_SECTION_WIDTH)
        header.setFixedHeight(40)

        self.setMinimumWidth(self._MIN_SECTION_WIDTH + self._VERTICAL_HEADER_WIDTH)

    def reset(self) -> None:
        """清空表格与缓存。"""
        self.setRowCount(0)
        self._piece_weights.clear()

    def update_piece_weights(self, piece_weights: list[float]) -> None:
        """更新件重列表，最新数据在顶部。"""
        if piece_weights == self._piece_weights:
            return

        if not piece_weights:
            self.reset()
            return

        self.setUpdatesEnabled(False)
        try:
            count = len(piece_weights)
            self.setRowCount(count)
            self.setVerticalHeaderLabels([str(i) for i in range(count, 0, -1)])
            self._fill_rows(piece_weights)
            self._piece_weights = piece_weights.copy()
            self.scrollToTop()
        finally:
            self.setUpdatesEnabled(True)

    def _fill_rows(self, data: list[float]) -> None:
        """填充格式化重量单元格（最新在顶部）。"""
        for row, weight in enumerate(reversed(data)):
            item = QTableWidgetItem(f"{weight:.{self._decimal_places}f}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.setItem(row, 0, item)

    def set_decimal_places(self, places: int) -> None:
        """切换小数位数并重绘已有行。"""
        if places == self._decimal_places:
            return
        self._decimal_places = places
        if not self._piece_weights:
            return
        self.setUpdatesEnabled(False)
        try:
            self._fill_rows(self._piece_weights)
        finally:
            self.setUpdatesEnabled(True)
