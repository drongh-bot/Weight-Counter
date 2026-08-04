# main.py
import logging
import sys

from PySide6.QtWidgets import QApplication

from app.controllers.main_controller import MainController
from app.core.log_config import setup_logging
from app.core.resource_manager import ResourceManager
from app.core.sound import SoundService
from app.presentation.ui import UiBridge
from app.services.config_service import ConfigService
from app.services.counter_service import CounterService
from app.services.csv_log_service import CsvLogService
from app.services.serial_service import SerialService
from app.services.weight_input_service import WeightInputService
from app.views.main_window import MainWindow

logger = logging.getLogger(__name__)


def main():
    """应用入口：组装 DI 依赖并启动 Qt 主循环。"""
    app = QApplication(sys.argv)

    setup_logging(ResourceManager.get_external_root() / "log")

    config_service = ConfigService()
    params = config_service.load(ResourceManager.get_external_root() / "config.toml")

    ui = UiBridge()
    serial_service = SerialService(params.timeout_millis)
    counter_service = CounterService(params)
    weight_input_service = WeightInputService(params)
    sound_service = SoundService()
    csv_log_service = CsvLogService()

    controller = MainController(
        ui=ui,
        serial_service=serial_service,
        counter_service=counter_service,
        weight_input_service=weight_input_service,
        sound_service=sound_service,
        csv_log_service=csv_log_service,
        params=params,
    )

    window = MainWindow(
        ui=ui,
        controller=controller,
        params=params,
        config_service=config_service,
    )
    window.show()

    exit_code = app.exec()

    try:
        controller.shutdown()
    except Exception:
        logger.exception("退出清理失败")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
