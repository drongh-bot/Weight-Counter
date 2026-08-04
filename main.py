# main.py
import logging
import sys

from PySide6.QtWidgets import QApplication

from app.controllers.main_controller import MainController
from app.core.log_config import setup_logging
from app.core.resource_manager import ResourceManager
from app.core.sound_player import SoundPlayer
from app.presentation.ui_bridge import UiBridge
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

    setup_logging(ResourceManager.get_external("log"))

    config_service = ConfigService()
    params = config_service.load(ResourceManager.get_external("config.toml"))

    ui_bridge = UiBridge()
    serial_service = SerialService(params.timeout_millis)
    counter_service = CounterService(params)
    weight_input_service = WeightInputService(params)
    sound_player = SoundPlayer()
    csv_log_service = CsvLogService()

    controller = MainController(
        ui_bridge=ui_bridge,
        serial_service=serial_service,
        counter_service=counter_service,
        weight_input_service=weight_input_service,
        sound_player=sound_player,
        csv_log_service=csv_log_service,
    )

    window = MainWindow(
        ui_bridge=ui_bridge,
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
