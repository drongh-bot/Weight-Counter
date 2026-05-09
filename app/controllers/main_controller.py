# app/controllers/main_controller.py
import logging
from enum import Enum, auto

from PySide6.QtCore import QObject

from app.models.biz_result import BizResult, BizState
from app.models.params import Params
from app.services.checker_service import CheckerService
from app.services.counter_service import CounterService
from app.services.csv_log_service import CsvLogService
from app.services.serial_service import SerialService
from app.services.sound_service import SoundService
from app.services.ui.models import ButtonState
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

        self.running: bool = False
        self._pending_action: PendingAction = PendingAction.NONE
        self._pending_force_pieces: int = 0

        self.serial_service.data_received.connect(self._on_raw_data)
        self.serial_service.timeout_detected.connect(self._on_timeout)
        self.serial_service.error_occurred.connect(self._on_serial_error)
        self.csv_log_service.error_occurred.connect(self._on_csv_error)

        self._update_ui(self.counter_service.current_result(), None)

    # ============================================================
    # UI Update
    # ============================================================
    def _update_ui(
        self,
        result: BizResult,
        weight: float | None,
        parse_ok: bool = True,
        comm_ok: bool = True,
        exception_text: str | None = None,
    ) -> None:
        abnormal = result.state == BizState.ABNORMAL
        button_state = ButtonState(
            start=not self.running,
            stop=self.running,
            clear=abnormal,
            force=abnormal,
        )
        self.ui_service.update(
            result,
            button_state,
            weight,
            parse_ok=parse_ok,
            comm_ok=comm_ok,
            exception_text=exception_text,
        )

    # ============================================================
    # Data Pipeline
    # ============================================================
    def _on_raw_data(self, raw: str) -> None:
        weight = self.checker_service.parse(raw)
        if weight is None:
            self._update_ui(self.counter_service.current_result(), None, parse_ok=False)
            return
        stable_weight = self.checker_service.check(weight)
        if stable_weight is None:
            self._update_ui(
                self.counter_service.current_result(), weight, parse_ok=True
            )
            return
        self._handle_pre_process(stable_weight)
        result = self.counter_service.process(stable_weight)
        self._handle_result(result, stable_weight)

    def _handle_pre_process(self, stable_weight: float) -> None:
        if self._pending_action is PendingAction.FORCE_ACCEPT:
            self.counter_service.force_accept(stable_weight, self._pending_force_pieces)
            self._pending_action = PendingAction.NONE
        elif self._pending_action is PendingAction.CLEAR_ABNORMAL:
            self.counter_service.clear_abnormal(stable_weight)
            self._pending_action = PendingAction.NONE

    def _handle_result(self, result: BizResult, stable_weight: float) -> None:
        self._update_ui(result, stable_weight, parse_ok=True)
        if self.counter_service.consume_abnormal_edge():
            self.sound_service.play_error()
        if self.counter_service.consume_target_edge():
            self.sound_service.play_alert()
        if result.added and result.weights:
            self.csv_log_service.record_production(
                result.weights[-1], result.total_pieces
            )

    # ============================================================
    # Event Handling
    # ============================================================
    def _on_timeout(self) -> None:
        self._update_ui(
            self.counter_service.current_result(), None, parse_ok=False, comm_ok=False
        )

    def _on_serial_error(self, msg: str) -> None:
        self._update_ui(
            self.counter_service.current_result(),
            None,
            parse_ok=False,
            comm_ok=False,
            exception_text=msg,
        )

    def _on_csv_error(self, msg: str) -> None:
        self._update_ui(self.counter_service.current_result(), None, exception_text=msg)

    # ============================================================
    # User Actions
    # ============================================================
    def force_accept(self, pieces: int) -> None:
        if self.running:
            self._pending_action = PendingAction.FORCE_ACCEPT
            self._pending_force_pieces = pieces

    def clear_abnormal(self) -> None:
        if self.running:
            self._pending_action = PendingAction.CLEAR_ABNORMAL

    # ============================================================
    # Lifecycle
    # ============================================================
    def _reset_all(self) -> None:
        self.counter_service.reset()
        self.checker_service.reset()
        self._update_ui(self.counter_service.current_result(), None)

    def start(self, port: str, baud: int) -> bool:
        self.running = True
        self._reset_all()
        try:
            self.serial_service.open(port, baud)
            return True
        except Exception as e:
            self.running = False
            self._update_ui(
                self.counter_service.current_result(),
                None,
                parse_ok=False,
                comm_ok=False,
                exception_text=str(e),
            )
            logger.exception("串口打开失败")
            return False

    def stop(self) -> None:
        self.running = False
        self._pending_action = PendingAction.NONE
        self._reset_all()
        self.serial_service.close()

    def shutdown(self) -> None:
        self.serial_service.close()
        self.csv_log_service.close()
        self.sound_service.stop()
