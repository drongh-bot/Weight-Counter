# app/views/main_window.py
import logging

from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent, QIcon
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
from app.presentation.count_display import build_count_display
from app.presentation.ui_bridge import UiBridge
from app.presentation.view_data import BarSnapshot, ControlStatus, LabelItem
from app.services.config_service import ConfigService
from app.version import __version__
from app.views.ui_generated.form import Ui_MainWindow
from app.views.widgets.piece_chart import PieceChart
from app.views.widgets.piece_table import PieceTable

logger = logging.getLogger(__name__)


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
        self.setWindowTitle(f"称重计数 v{__version__}")

        self.setWindowIcon(
            QIcon(str(ResourceManager.get_resource("app/resources/icons/app.ico")))
        )

        self.ui_bridge: UiBridge = ui_bridge
        self.controller: MainController = controller
        self.params: Params = params
        self.config_service: ConfigService = config_service

        self._init_central_widgets()
        self._init_status_labels()
        self._load_settings()
        self._load_params_to_ui()
        self._connect_bridge()
        self._bind_controls()

    def _init_central_widgets(self) -> None:
        """装配中间的件数表与散点图。"""
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.wgtPieceTable = PieceTable(self.params.start.decimal_places)
        self.wgtPieceChart = PieceChart(self.params.start.decimal_places)
        self.splitter.addWidget(self.wgtPieceTable)
        self.splitter.addWidget(self.wgtPieceChart)

        horizontal_layout = self.centralWidget().layout()
        assert isinstance(horizontal_layout, QHBoxLayout)
        horizontal_layout.addWidget(self.splitter, 1)

    def _init_status_labels(self) -> None:
        """装配底部状态栏的三格标签。"""
        self.lblParse = QLabel()
        self.lblComm = QLabel()
        self.lblMessage = QLabel()

        for lbl in [self.lblParse, self.lblComm, self.lblMessage]:
            lbl.setContentsMargins(5, 5, 5, 5)
            lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        bar = self.statusBar()
        bar.setStyleSheet("QStatusBar::item { border: none; }")
        bar.addWidget(self.lblParse, 1)
        bar.addWidget(self.lblComm, 1)
        bar.addWidget(self.lblMessage, 1)

    def _connect_bridge(self) -> None:
        """UiBridge 信号 → 本窗槽。"""
        self.ui_bridge.actual_weight_text_changed.connect(self.lblActWeight.setText)
        self.ui_bridge.bar_snapshot_changed.connect(self._on_bar_snapshot_changed)
        self.ui_bridge.control_status_changed.connect(self._on_control_status_changed)
        self.ui_bridge.count_snapshot_changed.connect(self._on_count_snapshot_changed)

    def _on_bar_snapshot_changed(self, data: BarSnapshot) -> None:
        """刷新状态栏三标签。"""
        self._apply_label(data.parse, self.lblParse)
        self._apply_label(data.comm, self.lblComm)
        self._apply_label(data.message, self.lblMessage)

    def _on_control_status_changed(self, state: ControlStatus) -> None:
        """同步按钮与 Start 参数控件的可用状态（target_pieces 不锁，改了立刻生效）。"""
        self.btnStart.setEnabled(state.start_enabled)
        self.btnStop.setEnabled(state.stop_enabled)
        self.btnForce.setEnabled(state.force_enabled)

        enabled = state.start_params_enabled
        self.dspnInitialMinWeight.setEnabled(enabled)
        self.dspnTolerancePercent.setEnabled(enabled)
        self.dspnStabilityThreshold.setEnabled(enabled)
        self.spnMaxBatchPieces.setEnabled(enabled)
        self.spnInitialSinglePieces.setEnabled(enabled)
        self.spnDecimalPlaces.setEnabled(enabled)

    def _on_count_snapshot_changed(self, snap: CountSnapshot) -> None:
        """刷新计件标签、表格与散点图。"""
        display = build_count_display(snap)

        self._apply_label(display.delta, self.lblDeltaWeight)
        self._apply_label(display.state, self.lblState)
        self.lblAvgWeight.setText(display.avg_text)
        self.lblTolHigh.setText(display.tol_high_text)
        self.lblTolLow.setText(display.tol_low_text)
        self.lblTotalPieces.setText(display.total_text)
        self.lblLastStableWeight.setText(display.last_stable_text)
        self.lblBaselineWeight.setText(display.baseline_text)

        self.wgtPieceTable.update_piece_weights(snap.piece_weights)
        self.wgtPieceChart.update_piece_weights(snap.piece_weights)

    def _apply_label(self, item: LabelItem, label: QLabel) -> None:
        """把 LabelItem 的文案与样式应用到 QLabel。"""
        label.setText(item.text)
        label.setStyleSheet(item.style)

    def _bind_controls(self) -> None:
        """按钮 / 参数旋钮 → 本窗方法。"""
        self.btnStart.clicked.connect(self.start)
        self.btnStop.clicked.connect(self.stop)
        self.btnForce.clicked.connect(self._on_force_clicked)

        self.dspnInitialMinWeight.valueChanged.connect(self._sync_ui_to_params)
        self.dspnTolerancePercent.valueChanged.connect(self._sync_ui_to_params)
        self.dspnStabilityThreshold.valueChanged.connect(self._sync_ui_to_params)
        self.spnMaxBatchPieces.valueChanged.connect(self._sync_ui_to_params)
        self.spnInitialSinglePieces.valueChanged.connect(self._sync_ui_to_params)
        self.spnDecimalPlaces.valueChanged.connect(self._sync_ui_to_params)
        self.spnTargetPieces.valueChanged.connect(self._sync_ui_to_params)

    def start(self) -> None:
        """Start：按 config.toml 里的串口参数打开串口并开始计件。"""
        self._sync_ui_to_params()
        if not self.controller.start(
            self.params.fixed.port, self.params.fixed.baud_rate
        ):
            QMessageBox.warning(self, "提示", f"无法打开串口 {self.params.fixed.port}")
            return

        places = self.params.start.decimal_places
        self.wgtPieceTable.set_decimal_places(places)
        self.wgtPieceChart.set_decimal_places(places)

    def stop(self) -> None:
        """Stop：停止计件并关闭串口。"""
        self.controller.stop()

    def _on_force_clicked(self) -> None:
        """读取强制片数并提交给控制器。"""
        pieces = self.spnForcePieces.value()
        if pieces <= 0:
            QMessageBox.warning(self, "提示", "请先输入强制片数")
            return
        self.controller.request_force_calibrate(pieces)
        self.spnForcePieces.setValue(0)

    def _save_params(self) -> None:
        """UI → Params 同步，再由 ConfigService 落盘。"""
        self._sync_ui_to_params()
        self.params.fixed.splitter_sizes = self.splitter.sizes()
        self.config_service.save(self.params)

    def _load_params_to_ui(self) -> None:
        """把 Params 里可调的字段写到对应控件。

        每次写入都屏蔽信号：否则 setValue 会触发 _sync_ui_to_params，
        把**还没轮到的控件的旧值**回写进 Params，冲掉刚设进去的新值。
        """

        def load(widget, value) -> None:
            widget.blockSignals(True)
            widget.setValue(value)
            widget.blockSignals(False)

        load(self.dspnInitialMinWeight, self.params.start.initial_min_weight)
        load(self.dspnTolerancePercent, self.params.start.tolerance_percent)
        load(self.dspnStabilityThreshold, self.params.start.stability_threshold)
        load(self.spnMaxBatchPieces, self.params.start.max_batch_pieces)
        load(self.spnInitialSinglePieces, self.params.start.initial_single_pieces)
        load(self.spnDecimalPlaces, self.params.start.decimal_places)
        load(self.spnTargetPieces, self.params.target_pieces)

    def _sync_ui_to_params(self) -> None:
        """把参数控件当前值写回共享 Params（写字段、不换子对象，否则共享会断）。"""
        self.params.start.initial_min_weight = self.dspnInitialMinWeight.value()
        self.params.start.tolerance_percent = self.dspnTolerancePercent.value()
        self.params.start.stability_threshold = self.dspnStabilityThreshold.value()
        self.params.start.max_batch_pieces = self.spnMaxBatchPieces.value()
        self.params.start.initial_single_pieces = self.spnInitialSinglePieces.value()
        self.params.start.decimal_places = self.spnDecimalPlaces.value()
        self.params.target_pieces = self.spnTargetPieces.value()

    def _load_settings(self) -> None:
        """恢复上次的分割条尺寸（配置写坏时退回默认）。"""
        sizes = self.params.fixed.splitter_sizes
        if not isinstance(sizes, list):
            sizes = [400, 600]
        else:
            try:
                sizes = [int(x) for x in sizes]
            except (TypeError, ValueError):
                logger.warning("splitter_sizes 格式错误, 使用默认值")
                sizes = [400, 600]
        self.splitter.setSizes(sizes)

    def closeEvent(self, event: QCloseEvent) -> None:
        """关闭窗口前存一次配置；真正的 shutdown 在 main.py 的 finally 里。"""
        self.hide()
        try:
            self._save_params()
        except Exception:
            logger.exception("关闭时保存配置失败")
        finally:
            event.accept()
