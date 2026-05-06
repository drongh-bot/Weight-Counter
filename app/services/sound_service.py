# app/services/sound_service.py
from PySide6.QtCore import QObject, Signal

from app.core.resource_manager import ResourceManager
from app.core.sound import SoundManager


class SoundService(QObject):
    """
    SoundService:
    - Wraps SoundManager
    - Captures underlying errors
    - Emits Qt signals to UI or Controller
    - Provides semantic business interfaces (play_add / play_error / play_alert)
    """

    soundError = Signal(str)  # report sound errors to UI

    def __init__(self):
        super().__init__()
        self.sound_manager = SoundManager.instance()

    # ============================================================
    # Error sound (counting abnormal)
    # ============================================================
    def play_error(self):
        self._play(ResourceManager.get_resource("app/resources/sounds/error.wav"))

    # ============================================================
    # Target reached alert sound
    # ============================================================
    def play_alert(self):
        self._play(ResourceManager.get_resource("app/resources/sounds/alert.wav"))

    # ============================================================
    # Stop all sounds
    # ============================================================
    def stop(self):
        self.sound_manager.stop()

    # ============================================================
    # Internal unified play logic
    # ============================================================
    def _play(self, file_name: str):
        success, error_msg = self.sound_manager.play(file_name)
        if not success:
            self.soundError.emit(error_msg)
