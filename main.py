# main.py
import logging
import sys

from PySide6.QtWidgets import QApplication

from app.controllers.main_controller import MainController
from app.core.log_config import setup_logging
from app.core.resource_manager import ResourceManager
from app.models.parameter_manager import ParameterManager
from app.services.checker_service import CheckerService
from app.services.counter_service import CounterService
from app.services.csv_log_service import CsvLogService
from app.services.serial_service import SerialService
from app.services.sound_service import SoundService
from app.services.ui.ui_service import UIService
from app.views.main_window import MainWindow

logger = logging.getLogger(__name__)


def main():
    app = QApplication(sys.argv)

    # ---------------- Logging ----------------
    setup_logging(ResourceManager.get_external_root() / "log")

    # ---------------- Parameters ----------------
    params = ParameterManager()
    params.load()

    # ---------------- Service Layer ----------------
    ui_service = UIService()
    serial_service = SerialService(params.serial_timeout_millis)
    counter_service = CounterService(params)
    checker_service = CheckerService(params)
    sound_service = SoundService()
    csv_log_service = CsvLogService()

    # ---------------- Controller ----------------
    controller = MainController(
        ui_service=ui_service,
        serial_service=serial_service,
        counter_service=counter_service,
        checker_service=checker_service,
        sound_service=sound_service,
        csv_log_service=csv_log_service,
        params=params,
    )

    # ---------------- UI Layer ----------------
    window = MainWindow(
        ui_service=ui_service,
        controller=controller,
        params=params,
    )
    window.show()

    # ---------------- Qt Main Loop ----------------
    exit_code = app.exec()

    # ---------------- Fallback Cleanup (Very Important) ----------------
    try:
        controller.shutdown()
    except Exception:
        logger.exception("shutdown error")

    sys.exit(exit_code)
if __name__ == "__main__":
    main()
