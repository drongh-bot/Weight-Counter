# app/controllers/main_controller.py
import logging

from app.core.sound_player import SoundPlayer
from app.models.count_snapshot import CountFrame, CountSnapshot
from app.presentation.status_bar import StatusBar
from app.presentation.ui_bridge import UiBridge
from app.presentation.view_models import BarSnapshot, ButtonStatus
from app.services.counter_service import CounterService
from app.services.csv_log_service import CsvLogService
from app.services.serial_service import SerialService
from app.services.weight_input_service import WeightInputService

logger = logging.getLogger(__name__)


class MainController:
    """把秤上的数据和界面串起来：来一包串口数据，就按顺序做完解析、稳重、计件、刷新界面。"""

    def __init__(
        self,
        ui_bridge: UiBridge,
        serial_service: SerialService,
        counter_service: CounterService,
        weight_input_service: WeightInputService,
        sound_player: SoundPlayer,
        csv_log_service: CsvLogService,
    ):
        """接上串口、计件、界面等依赖，并监听超时/串口错误/写日志错误。"""
        self.ui_bridge: UiBridge = ui_bridge
        self.serial_service: SerialService = serial_service
        self.counter_service: CounterService = counter_service
        self.weight_input_service: WeightInputService = weight_input_service
        self.sound_player: SoundPlayer = sound_player
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
        """开机时把件数区和底部提示刷成初始状态。"""
        self._sync_count_ui()
        self.ui_bridge.update_bar(self._bar.reset())

    def _button_status(self) -> ButtonStatus:
        """按是否在跑、是否在等强制校准，决定 Start/Stop/强制校准等按钮能不能点。"""
        pending_force = self._pending_force_pieces is not None
        return ButtonStatus(
            start_enabled=not self._is_running,
            stop_enabled=self._is_running,
            force_enabled=self._is_running and not pending_force,
            start_params_enabled=not self._is_running,
        )

    def _sync_button_status(self) -> None:
        """把按钮能不能点告诉界面。"""
        self.ui_bridge.update_button_status(self._button_status())

    def _clear_pending(self) -> None:
        """取消「等重量稳住再强制校准」。"""
        self._pending_force_pieces = None

    def _raw_mismatches_stable(self, raw_weight: float, stable_weight: float) -> bool:
        """当前跳动重量和已稳住的重量差太大 → 还不能做强制校准。"""
        return (
            abs(raw_weight - stable_weight)
            > self.weight_input_service.stability_threshold
        )

    def _clear_actual_weight(self) -> None:
        """界面上的「当前秤重」显示成占位符。"""
        self.ui_bridge.update_actual_weight(None, self.counter_service.decimal_places)

    def _sync_count_ui(self) -> None:
        """按当前件数刷新中间计件区，并清空当前秤重。"""
        snap = self.counter_service.snapshot()
        self.ui_bridge.update_count(snap)
        self._sync_button_status()
        self._clear_actual_weight()

    def _on_raw_data(self, raw_data: str) -> None:
        """秤送来一包数据时的处理顺序：

        读出重量 → 更新「当前秤重」
              → 判断重量稳不稳
              → 稳了才计件（或做挂起的强制校准）
              → 该响的响、该记生产的记，再刷新件数和底部提示
        """
        if not self._is_running:
            return

        weight = self.weight_input_service.parse(raw_data)

        if weight is None:
            self.ui_bridge.update_bar(self._bar.on_parse_fail())
            self._clear_actual_weight()
            return

        stable_weight = self.weight_input_service.stabilize(weight)
        self.ui_bridge.update_actual_weight(
            weight, self.counter_service.decimal_places
        )

        if self._pending_force_pieces is not None:
            if stable_weight is None or self._raw_mismatches_stable(
                weight, stable_weight
            ):
                self.ui_bridge.update_bar(self._bar.on_force_waiting_frame())
                return
        elif stable_weight is None:
            # 重量还在晃：先不计件，也不改底部提示（免得盖住异常/报错）
            return

        frame, bar = self._resolve_stable_frame(stable_weight)
        self._handle_frame(frame, stable_weight)
        self.ui_bridge.update_bar(bar)

    def _resolve_stable_frame(
        self, stable_weight: float
    ) -> tuple[CountFrame, BarSnapshot]:
        """重量已稳住：若在等强制校准就先做校准，否则正常加减件。"""
        if self._pending_force_pieces is None:
            frame = self.counter_service.process(stable_weight)
            return frame, self._bar.on_stable_frame(
                state=frame.state,
                target_edge=frame.target_edge,
                piece_added=frame.piece_added,
            )

        pieces = self._pending_force_pieces
        self._pending_force_pieces = None
        calibrated = self.counter_service.force_calibrate(stable_weight, pieces)
        if calibrated is None:
            # 失败只提示，不再 process（过轻时会 reset 清空已计件数）
            frame = self.counter_service.current_frame()
            return frame, self._bar.on_force_fail_frame(
                state=frame.state,
                target_edge=False,
                piece_added=False,
            )

        self._record_production(calibrated)
        return calibrated, self._bar.on_force_done_frame(
            state=calibrated.state,
            target_edge=calibrated.target_edge,
            piece_added=calibrated.piece_added,
        )

    def _handle_frame(self, frame: CountFrame, stable_weight: float) -> None:
        """刷新件数和当前秤重；刚进异常/刚达目标则播放提示音；有新件则记生产。"""
        self.ui_bridge.update_actual_weight(stable_weight, frame.decimal_places)
        self.ui_bridge.update_count(frame)
        self._sync_button_status()
        if frame.abnormal_edge:
            self.sound_player.play_error()
        if frame.target_edge:
            self.sound_player.play_alert()
        if frame.piece_added:
            self._record_production(frame)

    def _record_production(self, snap: CountSnapshot) -> None:
        """把最新一件的单重和当前总件数写入生产日志。"""
        if snap.piece_weights:
            self.csv_log_service.record_production(
                snap.piece_weights[-1],
                snap.total_pieces,
                snap.decimal_places,
            )

    def _on_timeout(self) -> None:
        """秤超时未回数据：底部提示等待，当前秤重清空。"""
        self.ui_bridge.update_bar(self._bar.on_timeout())
        self._clear_actual_weight()

    def _on_serial_error(self, msg: str) -> None:
        """串口故障：底部显示错误，当前秤重清空。"""
        self.ui_bridge.update_bar(self._bar.on_serial_error(msg))
        self._clear_actual_weight()

    def _on_csv_error(self, msg: str) -> None:
        """写生产日志失败：只改底部消息。"""
        self.ui_bridge.update_bar(self._bar.on_csv_error(msg))

    def request_force_calibrate(self, pieces: int) -> None:
        """操作员点了强制校准：记下片数，等重量稳住后再真正改单重/件数。"""
        if not self._is_running or pieces <= 0:
            return
        if self._pending_force_pieces is not None:
            return
        self._pending_force_pieces = pieces
        self._sync_button_status()
        self.ui_bridge.update_bar(self._bar.on_force_waiting_frame())

    def _reset_all(self) -> None:
        """件数清零、稳重状态清空，界面恢复初始。"""
        self.counter_service.reset()
        self.weight_input_service.reset()
        self._sync_count_ui()
        self.ui_bridge.update_bar(self._bar.reset())

    def start(self, port: str, baud: int) -> bool:
        """点 Start：套用当前界面参数、打开秤串口，开始收数计件。"""
        if self._is_running:
            return False
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
        """Start 失败（通常是串口打不开）：停下来并在底部显示原因。"""
        self._is_running = False
        self._sync_count_ui()
        self.ui_bridge.update_bar(self._bar.on_start_failed(str(error)))
        logger.exception("串口打开失败")

    def stop(self) -> None:
        """点 Stop：停止收数、清状态、关串口、停提示音。"""
        self._is_running = False
        self._clear_pending()
        self._reset_all()
        self.serial_service.close()
        self.sound_player.stop()

    def shutdown(self) -> None:
        """程序退出时关掉串口、生产日志和提示音。"""
        self.serial_service.close()
        self.csv_log_service.close()
        self.sound_player.stop()
