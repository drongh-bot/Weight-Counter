# app/views/main_window.py
import logging
from typing import NamedTuple

from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent, QIcon
from PySide6.QtSerialPort import QSerialPortInfo
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSplitter,
)

from app.controllers.main_controller import MainController
from app.core.resource_manager import ResourceManager
from app.models.count_snapshot import CountSnapshot
from app.models.params import Params
from app.presentation.count_labels import delta_style, state_label
from app.presentation.ui_bridge import UiBridge
from app.presentation.view_models import BarSnapshot, ButtonStatus, LabelItem
from app.services.config_service import ConfigService
from app.views.ui_generated.form import Ui_MainWindow
from app.views.widgets.piece_chart import PieceChart
from app.views.widgets.piece_table import PieceTable

logger = logging.getLogger(__name__)


class _ParamField(NamedTuple):
    """界面可调参数：Params 字段 ↔ 控件；lock_on_start 表示跑起来后锁住。"""

    attr: str
    widget: str
    cast: type
    lock_on_start: bool


_PARAM_FIELDS = (
    _ParamField("initial_min_weight", "dspnInitialMinWeight", float, True),
    _ParamField("tolerance_percent", "dspnTolerancePercent", float, True),
    _ParamField("stability_threshold", "dspnStabilityThreshold", float, True),
    _ParamField("max_batch_pieces", "spnMaxBatchPieces", int, True),
    _ParamField("initial_single_pieces", "spnInitialSinglePieces", int, True),
    _ParamField("target_pieces", "spnTargetPieces", int, False),
    _ParamField("decimal_places", "spnDecimalPlaces", int, True),
)


class MainWindow(QMainWindow, Ui_MainWindow):
    """主窗口：听 UiBridge 刷新界面；Start/Stop/强制校准/存配置交给控制器，不碰计件算法。"""

    def __init__(
        self,
        ui_bridge: UiBridge,
        controller: MainController,
        params: Params,
        config_service: ConfigService,
    ):
        """组装控件、加载配置并绑定信号。"""
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("称重计数 v1.4.0")

        self.setWindowIcon(
            QIcon(str(ResourceManager.get_resource("app/resources/icons/app.ico")))
        )

        self.ui_bridge: UiBridge = ui_bridge
        self.controller: MainController = controller
        self.params: Params = params
        self.config_service: ConfigService = config_service

        self._init_port_list()
        self._init_baud_rate_list()

        self._init_extra_widgets()

        self._load_settings()

        self._load_params_to_ui()

        self._connect_bridge()
        self._bind_controls()

    def _init_extra_widgets(self) -> None:
        """装配件数表、散点图与自定义状态栏标签。"""
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.wgtPieceTable = PieceTable(self.params.decimal_places)
        self.wgtPieceChart = PieceChart(self.params.decimal_places)
        self.splitter.addWidget(self.wgtPieceTable)
        self.splitter.addWidget(self.wgtPieceChart)

        horizontal_layout = self.centralWidget().layout()
        assert isinstance(horizontal_layout, QHBoxLayout)
        horizontal_layout.addWidget(self.splitter, 1)

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

    def _connect_bridge(self) -> None:
        """UiBridge 信号 → 本窗槽。"""
        self.ui_bridge.actual_weight_changed.connect(self.lblActWeight.setText)
        self.ui_bridge.bar_snapshot_changed.connect(self._on_bar_snapshot_changed)
        self.ui_bridge.button_status_changed.connect(self._on_button_status_changed)
        self.ui_bridge.count_changed.connect(self._on_count_changed)

    def _on_bar_snapshot_changed(self, data: BarSnapshot) -> None:
        """刷新状态栏三标签。"""
        self._apply_bar_label_item(data.parse, self.lblParse)
        self._apply_bar_label_item(data.comm, self.lblComm)
        self._apply_bar_label_item(data.message, self.lblMessage)

    def _on_button_status_changed(self, state: ButtonStatus) -> None:
        """同步按钮与 Start 参数控件的可用状态。"""
        self.btnStart.setEnabled(state.start_enabled)
        self.btnStop.setEnabled(state.stop_enabled)
        self.btnForce.setEnabled(state.force_enabled)
        for field in _PARAM_FIELDS:
            if field.lock_on_start:
                getattr(self, field.widget).setEnabled(state.start_params_enabled)

    def _on_count_changed(self, snap: CountSnapshot) -> None:
        """刷新计件标签、表格与散点图。"""
        dp = snap.decimal_places
        state = state_label(snap)

        self.lblDeltaWeight.setText(f"{snap.delta:.{dp}f}")
        self.lblDeltaWeight.setStyleSheet(delta_style(snap))

        self.lblState.setText(state.text)
        self.lblState.setStyleSheet(state.style)

        self.lblAvgWeight.setText(f"{snap.avg_weight:.{dp}f}")
        self.lblTolHigh.setText(f"{snap.tolerance_high:.{dp}f}")
        self.lblTolLow.setText(f"{snap.tolerance_low:.{dp}f}")
        self.lblTotalPieces.setText(str(snap.total_pieces))
        self.lblLastStableWeight.setText(f"{snap.last_stable_weight:.{dp}f}")
        self.lblBaselineWeight.setText(f"{snap.baseline_weight:.{dp}f}")

        self.wgtPieceTable.update_piece_weights(snap.piece_weights)
        self.wgtPieceChart.update_piece_weights(snap.piece_weights)

    def _apply_bar_label_item(self, item: LabelItem, label: QLabel) -> None:
        """把 LabelItem 的文案与样式应用到 QLabel。"""
        label.setText(item.text)
        label.setStyleSheet(item.style)

    def _bind_controls(self) -> None:
        """按钮 / 参数旋钮 → 本窗方法。"""
        self.btnStart.clicked.connect(self.start)
        self.btnStop.clicked.connect(self.stop)
        self.btnForce.clicked.connect(self.force_calibrate)
        self.btnSaveParams.clicked.connect(self.save_params)

        for field in _PARAM_FIELDS:
            getattr(self, field.widget).valueChanged.connect(self._sync_ui_to_params)

    def start(self) -> None:
        """Start：打开串口并开始计件。"""
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
        """Stop：停止计件并关闭串口。"""
        self.controller.stop()

    def force_calibrate(self) -> None:
        """读取强制片数并提交给控制器。"""
        pieces = int(self.spnForcePieces.value())
        if pieces <= 0:
            QMessageBox.warning(self, "提示", "请先输入强制片数")
            return
        self.controller.request_force_calibrate(pieces)
        self.spnForcePieces.setValue(0)

    def save_params(self) -> None:
        """UI → Params 同步，并将全部配置持久化到磁盘。"""
        self._sync_ui_to_params()
        self.params.port = self.cbPort.currentText()
        self.params.baud_rate = int(self.cbBaudRate.currentText())
        self.params.splitter_sizes = self.splitter.sizes()
        self.config_service.save(
            self.params, ResourceManager.get_external("config.toml")
        )

    def _load_params_to_ui(self) -> None:
        """把 Params 中的可编辑字段写到对应控件。"""
        for field in _PARAM_FIELDS:
            getattr(self, field.widget).setValue(getattr(self.params, field.attr))

    def _sync_ui_to_params(self) -> None:
        """把参数控件当前值写回共享 Params。"""
        for field in _PARAM_FIELDS:
            setattr(
                self.params,
                field.attr,
                field.cast(getattr(self, field.widget).value()),
            )

    def _init_port_list(self) -> None:
        """枚举并填充可用串口列表。"""
        self.cbPort.clear()
        ports = QSerialPortInfo.availablePorts()
        port_names = [port.portName() for port in ports]
        try:
            port_names.sort(key=lambda x: int(x.replace("COM", "")))
        except Exception:
            logger.warning("COM 端口排序回退")
            port_names.sort()
        self.cbPort.addItems(port_names)

    def _init_baud_rate_list(self) -> None:
        """填充常用波特率列表。"""
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
        """恢复分割条尺寸与串口/波特率选择。"""
        sizes = self.params.splitter_sizes
        if not isinstance(sizes, list):
            sizes = [400, 600]
        else:
            try:
                sizes = [int(x) for x in sizes]
            except (TypeError, ValueError):
                logger.warning("splitter_sizes 格式错误, 使用默认值")
                sizes = [400, 600]
        self.splitter.setSizes(sizes)

        self.cbPort.setCurrentText(self.params.port)
        self.cbBaudRate.setCurrentText(str(self.params.baud_rate))

    def closeEvent(self, event: QCloseEvent) -> None:
        """关闭前保存配置并 shutdown 控制器。"""
        self.hide()
        try:
            self.save_params()
        except Exception:
            logger.exception("关闭时保存配置失败")
        finally:
            self.controller.shutdown()
            event.accept()
