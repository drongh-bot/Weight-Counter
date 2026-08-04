# app/controllers/main_controller.py
import logging

from app.models.count_result import CountResult
from app.presentation.status_bar import ForceOutcome, StatusBar
from app.presentation.ui import UiBridge
from app.presentation.view_models import ButtonStatus
from app.services.counter_service import CounterService
from app.services.csv_log_service import CsvLogService
from app.services.serial_service import SerialService
from app.core.sound import SoundService
from app.services.weight_input_service import WeightInputService

logger = logging.getLogger(__name__)


class MainController:
    """主控制器 — 每帧串行编排，非流水线框架。"""

    def __init__(
        self,
        ui: UiBridge,
        serial_service: SerialService,
        counter_service: CounterService,
        weight_input_service: WeightInputService,
        sound_service: SoundService,
        csv_log_service: CsvLogService,
    ):
        """注入各服务并连接串口/CSV 信号。"""
        self.ui: UiBridge = ui
        self.serial_service: SerialService = serial_service
        self.counter_service: CounterService = counter_service
        self.weight_input_service: WeightInputService = weight_input_service
        self.sound_service: SoundService = sound_service
        self.csv_log_service: CsvLogService = csv_log_service

        self._is_running: bool = False
        self._pending_force_pieces: int | None = None
        self._bar = StatusBar()

        self.serial_service.data_received.connect(self._on_raw_data)
        self.serial_service.timeout_detected.connect(self._on_timeout)
        self.serial_service.error_occurred.connect(self._on_serial_error)
        self.csv_log_service.error_occurred.connect(self._on_csv_error)

        self._init_ui()

    def _init_ui(self) -> None:
        """启动时同步计件与状态栏初始显示。"""
        self._sync_count_ui()
        self.ui.update_bar(self._bar.reset())

    def _button_status(self) -> ButtonStatus:
        """按运行/强制校准挂起状态计算按钮可用性。"""
        pending_force = self._pending_force_pieces is not None
        return ButtonStatus(
            start_enabled=not self._is_running,
            stop_enabled=self._is_running,
            force_enabled=self._is_running and not pending_force,
            start_params_enabled=not self._is_running,
        )

    def _sync_button_status(self) -> None:
        """把按钮状态推到 UiBridge。"""
        self.ui.update_button_status(self._button_status())

    def _clear_pending(self) -> None:
        """清除挂起的强制校准。"""
        self._pending_force_pieces = None

    def _raw_mismatches_stable(self, raw_weight: float, stable_weight: float) -> bool:
        """实重与稳定重差异超过阈值时为 True（尚不可校准）。"""
        return (
            abs(raw_weight - stable_weight)
            > self.weight_input_service.stability_threshold
        )

    def _clear_actual_weight(self) -> None:
        """清空实重显示（用当前生效的小数位格式化占位）。"""
        self.ui.update_actual_weight(None, self.counter_service.decimal_places)

    def _sync_count_ui(self) -> None:
        """用当前计件快照刷新件数区，并清空实重显示。"""
        result = self.counter_service.current_result()
        self.ui.update_count(result)
        self._sync_button_status()
        self._clear_actual_weight()

    def _on_raw_data(self, raw_data: str) -> None:
        """串口一帧入口（串行编排）。

        原始串 → 解析 → 实重 UI
              → 稳定化（None 时可能直接返回且不改写状态栏）
              → 计件 → 边沿/声音/csv → 计件 UI + 状态栏
        """
        if not self._is_running:
            return

        weight = self.weight_input_service.parse(raw_data)

        if weight is None:
            self.ui.update_bar(self._bar.on_parse_fail())
            self._clear_actual_weight()
            return

        stable_weight = self.weight_input_service.stabilize(weight)
        result = self.counter_service.current_result()
        self.ui.update_actual_weight(weight, result.decimal_places)

        if self._pending_force_pieces is not None:
            if stable_weight is None or self._raw_mismatches_stable(weight, stable_weight):
                self.ui.update_bar(self._bar.on_force_waiting())
                return
        elif stable_weight is None:
            # 日常未稳定：不计件即可，勿改写状态栏（避免覆盖错误/异常等提示）
            return

        force, result = self._resolve_stable_frame(stable_weight)
        self._handle_result(result, stable_weight)
        self.ui.update_bar(
            self._bar.on_stable_frame(
                state=result.state,
                force=force,
                target_reached=result.target_edge,
                piece_added=result.added,
            )
        )

    def _resolve_stable_frame(
        self, stable_weight: float
    ) -> tuple[ForceOutcome, CountResult]:
        """本帧稳定重：优先执行挂起的强制校准，否则走正常计件。"""
        if self._pending_force_pieces is None:
            return ForceOutcome.NONE, self.counter_service.process(stable_weight)

        pieces = self._pending_force_pieces
        self._pending_force_pieces = None
        calibrated = self.counter_service.force_calibrate(stable_weight, pieces)
        if calibrated is None:
            return ForceOutcome.FAIL, self.counter_service.process(stable_weight)

        self._record_production(calibrated)
        return ForceOutcome.DONE, calibrated

    def _handle_result(self, result: CountResult, stable_weight: float) -> None:
        """刷新 UI，并按本帧边沿播放音效 / 记生产。"""
        self.ui.update_actual_weight(stable_weight, result.decimal_places)
        self.ui.update_count(result)
        self._sync_button_status()
        if result.abnormal_edge:
            self.sound_service.play_error()
        if result.target_edge:
            self.sound_service.play_alert()
        if result.added:
            self._record_production(result)

    def _record_production(self, result: CountResult) -> None:
        """有新件时写入生产 CSV。"""
        if result.piece_weights:
            self.csv_log_service.record_production(
                result.piece_weights[-1], result.total_pieces
            )

    def _on_timeout(self) -> None:
        """串口超时：更新状态栏并清空实重显示。"""
        self.ui.update_bar(self._bar.on_timeout())
        self._clear_actual_weight()

    def _on_serial_error(self, msg: str) -> None:
        """串口错误：更新状态栏并清空实重显示。"""
        self.ui.update_bar(self._bar.on_serial_error(msg))
        self._clear_actual_weight()

    def _on_csv_error(self, msg: str) -> None:
        """CSV 错误：仅更新状态栏消息。"""
        self.ui.update_bar(self._bar.on_csv_error(msg))

    def force_calibrate(self, pieces: int) -> None:
        """登记待强制校准片数，等待下一帧稳定重。"""
        if not self._is_running or pieces <= 0:
            return
        if self._pending_force_pieces is not None:
            return
        self._pending_force_pieces = pieces
        self._sync_button_status()
        self.ui.update_bar(self._bar.on_force_waiting())

    def _reset_all(self) -> None:
        """重置计件、稳重器与状态栏显示。"""
        self.counter_service.reset()
        self.weight_input_service.reset()
        self._sync_count_ui()
        self.ui.update_bar(self._bar.reset())

    def start(self, port: str, baud: int) -> bool:
        """Start：复制 START_SYNC 参数、打开串口。"""
        self._is_running = True
        self._reset_all()
        self.counter_service.apply_start_params()
        self.weight_input_service.apply_start_params()
        try:
            self.serial_service.open(port, baud)
            return True
        except Exception as e:
            self._handle_start_error(e)
            return False

    def _handle_start_error(self, error: Exception) -> None:
        """Start 失败：回滚运行标志并显示错误状态。"""
        self._is_running = False
        self._sync_count_ui()
        self.ui.update_bar(self._bar.on_start_failed(str(error)))
        logger.exception("串口打开失败")

    def stop(self) -> None:
        """Stop：重置状态并关闭串口。"""
        self._is_running = False
        self._clear_pending()
        self._reset_all()
        self.serial_service.close()
        self.sound_service.stop()

    def shutdown(self) -> None:
        """进程退出兜底：关闭串口、日志与音效。"""
        self.serial_service.close()
        self.csv_log_service.close()
        self.sound_service.stop()
