# app/controllers/main_controller.py
import logging

from PySide6.QtCore import QObject

from app.models.count_result import CountResult
from app.models.params import Params
from app.presentation.status_bar import ForceOutcome, StatusBar
from app.presentation.ui import Ui
from app.presentation.view_models import ButtonStatus
from app.services.counter_service import CounterService
from app.services.csv_log_service import CsvLogService
from app.services.serial_service import SerialService
from app.services.sound_service import SoundService
from app.services.weight_input_service import WeightInputService

logger = logging.getLogger(__name__)


class MainController(QObject):
    def __init__(
        self,
        ui: Ui,
        serial_service: SerialService,
        counter_service: CounterService,
        weight_input_service: WeightInputService,
        sound_service: SoundService,
        csv_log_service: CsvLogService,
        params: Params,
    ):
        super().__init__()

        self.ui: Ui = ui
        self.serial_service: SerialService = serial_service
        self.counter_service: CounterService = counter_service
        self.weight_input_service: WeightInputService = weight_input_service
        self.sound_service: SoundService = sound_service
        self.csv_log_service: CsvLogService = csv_log_service
        self.params: Params = params

        self._is_running: bool = False
        self._pending_force_pieces: int | None = None
        self._bar = StatusBar()

        self.serial_service.data_received.connect(self._on_raw_data)
        self.serial_service.timeout_detected.connect(self._on_timeout)
        self.serial_service.error_occurred.connect(self._on_serial_error)
        self.csv_log_service.error_occurred.connect(self._on_csv_error)

        self._init_ui()

    def _init_ui(self) -> None:
        self._sync_count_ui()
        self.ui.update_bar(self._bar.reset())

    def _button_status(self) -> ButtonStatus:
        pending_force = self._pending_force_pieces is not None
        return ButtonStatus(
            start_enabled=not self._is_running,
            stop_enabled=self._is_running,
            force_enabled=self._is_running and not pending_force,
            start_params_enabled=not self._is_running,
        )

    def _sync_button_status(self) -> None:
        self.ui.update_button_status(self._button_status())

    def _clear_pending(self) -> None:
        self._pending_force_pieces = None

    def _raw_mismatches_stable(self, raw_weight: float, stable_weight: float) -> bool:
        """True when actual and stable weight differ beyond tolerance (not ready to calibrate)."""
        return abs(raw_weight - stable_weight) > self.params.stability_threshold

    def _sync_count_ui(self) -> None:
        result = self.counter_service.current_result()
        self.ui.update_count(result)
        self._sync_button_status()
        self.ui.update_actual_weight(None, result.decimal_places)

    # ============================================================
    # Data Pipeline
    # ============================================================
    def _on_raw_data(self, raw_data: str) -> None:
        if not self._is_running:
            return

        weight = self.weight_input_service.parse(raw_data)

        if weight is None:
            self.ui.update_bar(self._bar.on_parse_fail())
            self.ui.update_actual_weight(
                None, self.counter_service.current_result().decimal_places
            )
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

        force = self._apply_pending_force(stable_weight)
        result = self.counter_service.process(stable_weight)
        target_reached, piece_added = self._handle_result(result, stable_weight)
        self.ui.update_bar(
            self._bar.on_stable_frame(
                state=result.state,
                force=force,
                target_reached=target_reached,
                piece_added=piece_added,
            )
        )

    def _apply_pending_force(self, stable_weight: float) -> ForceOutcome:
        if self._pending_force_pieces is None:
            return ForceOutcome.NONE
        pieces = self._pending_force_pieces
        self._pending_force_pieces = None
        if self.counter_service.force_calibrate(stable_weight, pieces):
            self._record_production(self.counter_service.current_result())
            return ForceOutcome.DONE
        return ForceOutcome.FAIL

    def _handle_result(
        self, result: CountResult, stable_weight: float
    ) -> tuple[bool, bool]:
        self.ui.update_actual_weight(stable_weight, result.decimal_places)
        self.ui.update_count(result)
        self._sync_button_status()
        target_reached, piece_added = self._handle_edge_events(result)
        if result.added:
            self._record_production(result)
        return target_reached, piece_added

    def _handle_edge_events(self, result: CountResult) -> tuple[bool, bool]:
        if self.counter_service.consume_abnormal_edge():
            self.sound_service.play_error()

        target_reached = self.counter_service.consume_target_edge()
        if target_reached:
            self.sound_service.play_alert()
        piece_added = result.added
        return target_reached, piece_added

    def _record_production(self, result: CountResult) -> None:
        if result.piece_weights:
            self.csv_log_service.record_production(
                result.piece_weights[-1], result.total_pieces
            )

    # ============================================================
    # Event Handling
    # ============================================================
    def _on_timeout(self) -> None:
        self.ui.update_bar(self._bar.on_timeout())
        self.ui.update_actual_weight(
            None, self.counter_service.current_result().decimal_places
        )

    def _on_serial_error(self, msg: str) -> None:
        self.ui.update_bar(self._bar.on_serial_error(msg))
        self.ui.update_actual_weight(
            None, self.counter_service.current_result().decimal_places
        )

    def _on_csv_error(self, msg: str) -> None:
        self.ui.update_bar(self._bar.on_csv_error(msg))

    # ============================================================
    # User Actions
    # ============================================================
    def force_calibrate(self, pieces: int) -> None:
        if not self._is_running or pieces <= 0:
            return
        if self._pending_force_pieces is not None:
            return
        self._pending_force_pieces = pieces
        self._sync_button_status()
        self.ui.update_bar(self._bar.on_force_waiting())

    # ============================================================
    # Lifecycle
    # ============================================================
    def _reset_all(self) -> None:
        self.counter_service.reset()
        self.weight_input_service.reset()
        self._sync_count_ui()
        self.ui.update_bar(self._bar.reset())

    def start(self, port: str, baud: int) -> bool:
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
        self._is_running = False
        self._sync_count_ui()
        self.ui.update_bar(self._bar.on_start_failed(str(error)))
        logger.exception("串口打开失败")

    def stop(self) -> None:
        self._is_running = False
        self._clear_pending()
        self._reset_all()
        self.serial_service.close()
        self.sound_service.stop()

    def shutdown(self) -> None:
        self.serial_service.close()
        self.csv_log_service.close()
        self.sound_service.stop()
