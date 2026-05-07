from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
)


class PieceTable(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._data: list[float] = []

        self.setColumnCount(1)
        self.setHorizontalHeaderLabels(["重量"])

        # Enable vertical header to display row index
        vertical_header = self.verticalHeader()
        vertical_header.setVisible(True)
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

    def reset(self):
        self.setRowCount(0)
        self._data.clear()

    def update_table(self, new_data: list[float], decimal_places: int = 2) -> None:
        """Newest data at the top."""
        if new_data == self._data:
            return

        self.setUpdatesEnabled(False)
        try:
            count = len(new_data)
            self.setRowCount(count)

            # Row index: count -> 1
            labels = [str(i) for i in range(count, 0, -1)]
            self.setVerticalHeaderLabels(labels)

            # Fill data (newest at the top)
            for row, weight in enumerate(reversed(new_data)):
                item = QTableWidgetItem(f"{weight:.{decimal_places}f}")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.setItem(row, 0, item)

            self._data = new_data.copy()
            self.scrollToTop()

        finally:
            self.setUpdatesEnabled(True)
