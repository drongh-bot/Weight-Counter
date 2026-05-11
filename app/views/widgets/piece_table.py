from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
)


class PieceTable(QTableWidget):
    def __init__(self, decimal_places: int = 2, parent=None) -> None:
        super().__init__(parent)

        self._piece_weights: list[float] = []
        self._decimal_places: int = decimal_places

        self.setColumnCount(1)
        self.setHorizontalHeaderLabels(["重量"])

        # Enable vertical header to display row index
        vertical_header = self.verticalHeader()
        vertical_header.setFixedWidth(40)

        # Key: align index to the right
        vertical_header.setDefaultAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )

        # Disable editing
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        # Column width strategy
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setMinimumSectionSize(100)

        # Table minimum width
        self.setMinimumWidth(100 + 40)

        # Key: increase header height
        header.setFixedHeight(40)

    def reset(self) -> None:
        self.setRowCount(0)
        self._piece_weights.clear()

    def _fill_rows(self, data: list[float]) -> None:
        """Fill cells with formatted weights (newest at top)."""
        for row, weight in enumerate(reversed(data)):
            item = QTableWidgetItem(f"{weight:.{self._decimal_places}f}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.setItem(row, 0, item)

    def update_table(self, new_data: list[float]) -> None:
        """Newest data at the top."""
        if new_data == self._piece_weights:
            return

        self.setUpdatesEnabled(False)
        try:
            count = len(new_data)
            self.setRowCount(count)

            labels = [str(i) for i in range(count, 0, -1)]
            self.setVerticalHeaderLabels(labels)

            self._fill_rows(new_data)

            self._piece_weights = new_data.copy()
            self.scrollToTop()

        finally:
            self.setUpdatesEnabled(True)

    def set_decimal_places(self, places: int) -> None:
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
