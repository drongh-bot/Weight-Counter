# app/services/sound_service.py
import logging

from PySide6.QtCore import QObject, Signal

from app.core.resource_manager import ResourceManager
from app.core.sound import SoundManager

logger = logging.getLogger(__name__)


class SoundService(QObject):
    """
    SoundService:
    - Wraps SoundManager
    - Captures underlying errors
    - Emits Qt signals to UI or Controller
    - Provides semantic business interfaces (play_add / play_error / play_alert)
    """

    error_occurred = Signal(str)  # report sound errors to UI

    def __init__(self) -> None:
        super().__init__()
        self.sound_manager = SoundManager()

    # ============================================================
    # Error sound (counting abnormal)
    # ============================================================
    def play_error(self) -> None:
        self._play(ResourceManager.get_resource("app/resources/sounds/error.wav"))

    # ============================================================
    # Target reached alert sound
    # ============================================================
    def play_alert(self) -> None:
        self._play(ResourceManager.get_resource("app/resources/sounds/alert.wav"))

    # ============================================================
    # Stop all sounds
    # ============================================================
    def stop(self) -> None:
        self.sound_manager.stop()

    # ============================================================
    # Internal unified play logic
    # ============================================================
    def _play(self, file_name: str) -> None:
        success, error_msg = self.sound_manager.play(file_name)
        if not success:
            logger.error("播放失败: %s", error_msg)
            self.error_occurred.emit(error_msg)
