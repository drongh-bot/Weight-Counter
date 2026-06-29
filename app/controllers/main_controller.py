# app/controllers/main_controller.py
import logging
from enum import Enum, auto

from PySide6.QtCore import QObject

from app.models.biz_result import BizResult
from app.models.counter_state import CounterState
from app.models.params import Params
from app.services.checker_service import CheckerService
from app.services.counter_service import CounterService
from app.services.csv_log_service import CsvLogService
from app.services.serial_service import SerialService
from app.services.sound_service import SoundService
from app.services.ui.models import ButtonStatus
from app.services.ui.ui_service import UIService

logger = logging.getLogger(__name__)


class PendingAction(Enum):
    NONE = auto()
    FORCE_ACCEPT = auto()
    CLEAR_ABNORMAL = auto()


class MainController(QObject):
    def __init__(
        self,
        ui_service: UIService,
        serial_service: SerialService,
        counter_service: CounterService,
        checker_service: CheckerService,
        sound_service: SoundService,
        csv_log_service: CsvLogService,
        params: Params,
    ):
        super().__init__()

        self.ui_service: UIService = ui_service
        self.serial_service: SerialService = serial_service
        self.counter_service: CounterService = counter_service
        self.checker_service: CheckerService = checker_service
        self.sound_service: SoundService = sound_service
        self.csv_log_service: CsvLogService = csv_log_service
        self.params: Params = params

        self._is_active: bool = False
        self._pending_action: PendingAction = PendingAction.NONE
        self._pending_force_pieces: int = 0

        self.serial_service.data_received.connect(self._on_raw_data)
        self.serial_service.timeout_detected.connect(self._on_timeout)
        self.serial_service.error_occurred.connect(self._on_serial_error)
        self.csv_log_service.error_occurred.connect(self._on_csv_error)

        self._init_ui()

    def _init_ui(self) -> None:
        self._sync_biz_ui()
        self.ui_service.update_bar_status()

    @staticmethod
    def _button_status(state: CounterState, is_active: bool) -> ButtonStatus:
        abnormal = state == CounterState.ABNORMAL
        return ButtonStatus(
            start=not is_active,
            stop=is_active,
            clear=abnormal,
            force=abnormal,
        )

    def _sync_biz_ui(self) -> None:
        result = self.counter_service.current_result()
        self.ui_service.update_biz(result)
        self.ui_service.update_button_status(
            self._button_status(result.state, self._is_active)
        )
        self.ui_service.update_actual_weight(None, result.decimal_places)

    # ============================================================
    # Data Pipeline
    # ============================================================
    def _on_raw_data(self, raw_data: str) -> None:
        weight = self.checker_service.parse(raw_data)

        if weight is None:
            self.ui_service.update_bar_status(parse_ok=False)
            return
        self.ui_service.update_bar_status(parse_ok=True)

        stable_weight = self.checker_service.check(weight)
        result = self.counter_service.current_result()
        self.ui_service.update_actual_weight(weight, result.decimal_places)

        if stable_weight is None:
            return

        self._apply_pending_action(stable_weight)
        result = self.counter_service.process(stable_weight)
        self._handle_result(result, stable_weight)

    def _apply_pending_action(self, stable_weight: float) -> None:
        if self._pending_action is PendingAction.FORCE_ACCEPT:
            self.counter_service.force_accept(stable_weight, self._pending_force_pieces)
        elif self._pending_action is PendingAction.CLEAR_ABNORMAL:
            self.counter_service.clear_abnormal(stable_weight)
        self._pending_action = PendingAction.NONE

    def _handle_result(self, result: BizResult, stable_weight: float) -> None:
        self.ui_service.update_actual_weight(stable_weight, result.decimal_places)
        self.ui_service.update_biz(result)
        self.ui_service.update_button_status(
            self._button_status(result.state, self._is_active)
        )
        self._handle_sound_events()
        self._handle_logging(result)

    def _handle_sound_events(self) -> None:
        if self.counter_service.consume_abnormal_edge():
            self.sound_service.play_error()
        if self.counter_service.consume_target_edge():
            self.sound_service.play_alert()

    def _handle_logging(self, result: BizResult) -> None:
        if result.added and result.weights:
            self.csv_log_service.record_production(
                result.weights[-1], result.total_pieces
            )

    # ============================================================
    # Event Handling
    # ============================================================
    def _on_timeout(self) -> None:
        self.ui_service.update_bar_status(comm_ok=False)
        self.ui_service.update_actual_weight(None, self.counter_service.current_result().decimal_places)

    def _on_serial_error(self, msg: str) -> None:
        self.ui_service.update_bar_status(comm_ok=False, exception_text=msg)
        self.ui_service.update_actual_weight(None, self.counter_service.current_result().decimal_places)

    def _on_csv_error(self, msg: str) -> None:
        self.ui_service.update_bar_status(exception_text=msg)

    # ============================================================
    # User Actions
    # ============================================================
    def force_accept(self, pieces: int) -> None:
        if self._is_active:
            self._pending_action = PendingAction.FORCE_ACCEPT
            self._pending_force_pieces = pieces

    def clear_abnormal(self) -> None:
        if self._is_active:
            self._pending_action = PendingAction.CLEAR_ABNORMAL

    # ============================================================
    # Lifecycle
    # ============================================================
    def _reset_all(self) -> None:
        self.counter_service.reset()
        self.checker_service.reset()
        self._sync_biz_ui()

    def start(self, port: str, baud: int) -> bool:
        self._is_active = True
        self._reset_all()
        self.counter_service.apply_params()
        self.checker_service.apply_params()
        try:
            self.serial_service.open(port, baud)
            return True
        except Exception as e:
            self._handle_start_error(e)
            return False

    def _handle_start_error(self, error: Exception) -> None:
        self._is_active = False
        self._sync_biz_ui()
        self.ui_service.update_bar_status(
            parse_ok=False, comm_ok=False, exception_text=str(error)
        )
        logger.exception("串口打开失败")

    def stop(self) -> None:
        self._is_active = False
        self._pending_action = PendingAction.NONE
        self._reset_all()
        self.serial_service.close()
        self.sound_service.stop()

    def shutdown(self) -> None:
        self.serial_service.close()
        self.csv_log_service.close()
        self.sound_service.stop()
