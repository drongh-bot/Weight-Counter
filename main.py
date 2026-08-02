# main.py
import logging
import sys

from PySide6.QtWidgets import QApplication

from app.controllers.main_controller import MainController
from app.core.log_config import setup_logging
from app.core.resource_manager import ResourceManager
from app.services.config_service import ConfigService
from app.services.counter_service import CounterService
from app.services.csv_log_service import CsvLogService
from app.services.serial_service import SerialService
from app.services.sound_service import SoundService
from app.presentation.ui_service import UIService
from app.services.weight_input_service import WeightInputService
from app.views.main_window import MainWindow

logger = logging.getLogger(__name__)


def main():
    app = QApplication(sys.argv)

    # ---------------- Logging ----------------
    setup_logging(ResourceManager.get_external_root() / "log")

    # ---------------- Parameters ----------------
    config_service = ConfigService()
    params = config_service.load(ResourceManager.get_external_root() / "config.toml")

    # ---------------- Service Layer ----------------
    ui_service = UIService()
    serial_service = SerialService(params.timeout_millis)
    counter_service = CounterService(params)
    weight_input_service = WeightInputService(params)
    sound_service = SoundService()
    csv_log_service = CsvLogService()

    # ---------------- Controller ----------------
    controller = MainController(
        ui_service=ui_service,
        serial_service=serial_service,
        counter_service=counter_service,
        weight_input_service=weight_input_service,
        sound_service=sound_service,
        csv_log_service=csv_log_service,
        params=params,
    )

    # ---------------- UI Layer ----------------
    window = MainWindow(
        ui_service=ui_service,
        controller=controller,
        params=params,
        config_service=config_service,
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
