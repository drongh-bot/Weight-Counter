# app/core/sound.py
from __future__ import annotations

import os
import winsound


class SoundManager:
    """
    Low-level sound driver:
    - No Qt dependency
    - No signals
    - No UI interaction
    - Only responsible for playing sounds
    """

    _instance: SoundManager | None = None

    def __new__(cls) -> "SoundManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        pass

    def play(self, full_path: str, repeat: bool = False) -> tuple[bool, str]:
        """
        Return (success, error_message)
        success = True means playback succeeded
        success = False means playback failed, error_message contains the reason
        """
        self.stop()

        if not os.path.exists(full_path):
            return False, f"Sound file not found: {full_path}"

        flags = winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT
        if repeat:
            flags |= winsound.SND_LOOP

        try:
            winsound.PlaySound(full_path, flags)
            return True, ""
        except Exception as e:
            return False, f"Failed to play sound: {full_path} ({e})"

    def stop(self) -> None:
        winsound.PlaySound(None, winsound.SND_PURGE)
