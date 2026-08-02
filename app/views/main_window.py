# app/views/main_window.py
import logging

from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent, QIcon
from PySide6.QtSerialPort import QSerialPortInfo
from PySide6.QtWidgets import (
    QLabel,
    QMainWindow,
    QMessageBox,
    QSplitter,
)

from app.controllers.main_controller import MainController
from app.core.resource_manager import ResourceManager
from app.models.params import Params
from app.services.config_service import ConfigService
from app.presentation.ui_service import UIService
from app.presentation.view_models import (
    BarStatus,
    ButtonStatus,
    CountSnapshot,
    LabelItem,
)
from app.views.ui_generated.form import Ui_MainWindow
from app.views.widgets.piece_chart import PieceChart
from app.views.widgets.piece_table import PieceTable

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(
        self,
        ui_service: UIService,
        controller: MainController,
        params: Params,
        config_service: ConfigService,
    ):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("称重计数 v1.3.5")

        self.setWindowIcon(
            QIcon(ResourceManager.get_resource("app/resources/icons/app.ico"))
        )

        self.ui_service: UIService = ui_service
        self.controller: MainController = controller
        self.params: Params = params
        self.config_service: ConfigService = config_service

        self._init_port_list()
        self._init_baud_rate_list()

        self._init_extra_widgets()

        self._load_settings()

        self._load_params_to_ui()

        self._bind_ui_service_signals()
        self._bind_ui_signals()

        # Proactively refresh the bottom status labels once after init
        self.ui_service.refresh()

    def _init_extra_widgets(self) -> None:
        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        self.wgtPieceTable = PieceTable(self.params.decimal_places)
        self.wgtPieceChart = PieceChart(self.params.decimal_places)

        self.splitter.addWidget(self.wgtPieceTable)
        self.splitter.addWidget(self.wgtPieceChart)

        self.rightPanel.layout().addWidget(self.splitter)

        self.lblParse = QLabel()
        self.lblComm = QLabel()
        self.lblMessage = QLabel()

        for lbl in [self.lblParse, self.lblComm, self.lblMessage]:
            lbl.setContentsMargins(5, 5, 5, 5)
            lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        status_bar = self.statusBar()
        status_bar.setStyleSheet("QStatusBar::item { border: none; }")
        status_bar.addWidget(self.lblParse, 1)
        status_bar.addWidget(self.lblComm, 1)
        status_bar.addWidget(self.lblMessage, 1)

    def _bind_ui_service_signals(self) -> None:
        self.ui_service.actual_weight_changed.connect(self.lblActWeight.setText)
        self.ui_service.bar_status_changed.connect(self._on_bar_status_changed)
        self.ui_service.button_status_changed.connect(self._on_button_status_changed)
        self.ui_service.count_changed.connect(self._on_count_changed)

    def _on_bar_status_changed(self, data: BarStatus) -> None:
        self._apply_bar_label_item(data.parse, self.lblParse)
        self._apply_bar_label_item(data.comm, self.lblComm)
        self._apply_bar_label_item(data.message, self.lblMessage)

    def _on_button_status_changed(self, state: ButtonStatus) -> None:
        self.btnStart.setEnabled(state.start_enabled)
        self.btnStop.setEnabled(state.stop_enabled)
        self.btnClear.setEnabled(state.clear_enabled)
        self.btnForce.setEnabled(state.force_enabled)

    def _on_count_changed(self, snap: CountSnapshot) -> None:
        try:
            self.lblDeltaWeight.setText(snap.delta_weight.text)
            self.lblDeltaWeight.setStyleSheet(snap.delta_weight.style)

            self.lblState.setText(snap.state.text)
            self.lblState.setStyleSheet(snap.state.style)

            self.lblAvgWeight.setText(snap.avg_weight)
            self.lblTolHigh.setText(snap.tolerance_high)
            self.lblTolLow.setText(snap.tolerance_low)
            self.lblTotalPieces.setText(snap.total_pieces)
            self.lblLastStableWeight.setText(snap.last_stable_weight)
            self.lblBaselineWeight.setText(snap.baseline_weight)

            self.wgtPieceTable.update_piece_weights(snap.piece_weights)
            self.wgtPieceChart.update_piece_weights(snap.piece_weights)

        except Exception as e:
            logger.exception("UI更新失败")
            QMessageBox.critical(self, "错误", f"UI更新时出错: {e}")

    def _apply_bar_label_item(self, item: LabelItem, label: QLabel) -> None:
        label.setText(item.text)
        label.setStyleSheet(item.style)

    def _bind_ui_signals(self) -> None:
        self.btnStart.clicked.connect(self.start)
        self.btnStop.clicked.connect(self.stop)
        self.btnForce.clicked.connect(self.force_calibrate)
        self.btnClear.clicked.connect(self.clear_abnormal)
        self.btnSaveParams.clicked.connect(self.save_params)

        self.dspnInitialMinWeight.valueChanged.connect(self._sync_ui_to_params)
        self.dspnTolerancePercent.valueChanged.connect(self._sync_ui_to_params)
        self.dspnStabilityThreshold.valueChanged.connect(self._sync_ui_to_params)
        self.spnMaxBatchPieces.valueChanged.connect(self._sync_ui_to_params)
        self.spnInitialSinglePieces.valueChanged.connect(self._sync_ui_to_params)
        self.spnForcePieces.valueChanged.connect(self._sync_ui_to_params)
        self.spnTargetPieces.valueChanged.connect(self._sync_ui_to_params)
        self.spnDecimalPlaces.valueChanged.connect(self._sync_ui_to_params)

    def start(self) -> None:
        port = self.cbPort.currentText()
        baud_rate = int(self.cbBaudRate.currentText())

        if not port:
            QMessageBox.warning(self, "提示", "请选择串口")
            return

        self._sync_ui_to_params()
        if not self.controller.start(port, baud_rate):
            QMessageBox.warning(self, "提示", f"无法打开串口 {port}")
            return

        places = self.params.decimal_places
        self.wgtPieceTable.set_decimal_places(places)
        self.wgtPieceChart.set_decimal_places(places)

    def stop(self) -> None:
        self.controller.stop()

    def force_calibrate(self) -> None:
        pieces = int(self.spnForcePieces.value())
        if pieces <= 0:
            QMessageBox.warning(self, "提示", "请先输入强制片数")
            return
        self.controller.force_calibrate(pieces)
        self.spnForcePieces.setValue(0)

    def clear_abnormal(self) -> None:
        self.controller.clear_abnormal()

    def save_params(self) -> None:
        """Sync UI → params, then persist all config to disk."""
        self._sync_ui_to_params()
        self.params.port = self.cbPort.currentText()
        self.params.baud_rate = int(self.cbBaudRate.currentText())
        self.params.splitter_sizes = self.splitter.sizes()
        self.config_service.save(
            self.params, ResourceManager.get_external_root() / "config.toml"
        )

    def _load_params_to_ui(self) -> None:
        self.dspnInitialMinWeight.setValue(self.params.initial_min_weight)
        self.dspnTolerancePercent.setValue(self.params.tolerance_percent)
        self.dspnStabilityThreshold.setValue(self.params.stability_threshold)
        self.spnMaxBatchPieces.setValue(self.params.max_batch_pieces)
        self.spnInitialSinglePieces.setValue(self.params.initial_single_pieces)
        self.spnTargetPieces.setValue(self.params.target_pieces)
        self.spnDecimalPlaces.setValue(self.params.decimal_places)

    def _sync_ui_to_params(self) -> None:
        self.params.initial_min_weight = float(self.dspnInitialMinWeight.value())
        self.params.tolerance_percent = float(self.dspnTolerancePercent.value())
        self.params.stability_threshold = float(self.dspnStabilityThreshold.value())
        self.params.max_batch_pieces = int(self.spnMaxBatchPieces.value())
        self.params.initial_single_pieces = int(self.spnInitialSinglePieces.value())
        self.params.target_pieces = int(self.spnTargetPieces.value())
        self.params.decimal_places = int(self.spnDecimalPlaces.value())

    def _init_port_list(self) -> None:
        self.cbPort.clear()
        ports = QSerialPortInfo.availablePorts()
        port_names = [port.portName() for port in ports]
        try:
            port_names.sort(key=lambda x: int(x.replace("COM", "")))
        except Exception:
            logger.warning("COM端口排序回退")
            port_names.sort()
        self.cbPort.addItems(port_names)

    def _init_baud_rate_list(self) -> None:
        self.cbBaudRate.clear()
        baud_rate_list = [
            "1200",
            "2400",
            "4800",
            "9600",
            "19200",
            "38400",
            "57600",
            "115200",
        ]
        self.cbBaudRate.addItems(baud_rate_list)

    def _load_settings(self) -> None:
        sizes = self.params.splitter_sizes
        if not isinstance(sizes, list):
            sizes = [400, 600]
        try:
            sizes = [int(x) for x in sizes]
        except Exception:
            logger.warning("splitter_sizes格式错误, 使用默认值")
            sizes = [400, 600]
        self.splitter.setSizes(sizes)

        self.cbPort.setCurrentText(self.params.port)
        self.cbBaudRate.setCurrentText(str(self.params.baud_rate))

    # ============================================================
    # Close event
    # ============================================================
    def closeEvent(self, event: QCloseEvent) -> None:
        self.hide()
        try:
            self.save_params()
        finally:
            self.controller.shutdown()
            event.accept()
