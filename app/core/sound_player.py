# app/core/sound_player.py
from __future__ import annotations

import logging
import os
import winsound

from pathlib import Path

from app.core.resource_manager import ResourceManager

logger = logging.getLogger(__name__)


class SoundPlayer:
    """播放错误/告警 wav。无 Qt、非单例 — 由 main 注入唯一实例。"""

    def play_error(self) -> None:
        """播放错误提示音。"""
        self._play(ResourceManager.get_resource("app/resources/sounds/error.wav"))

    def play_alert(self) -> None:
        """播放目标达成告警音。"""
        self._play(ResourceManager.get_resource("app/resources/sounds/alert.wav"))

    def stop(self) -> None:
        """停止当前播放。"""
        winsound.PlaySound(None, winsound.SND_PURGE)

    def _play(self, full_path: Path | str) -> None:
        """异步播放一次 wav。"""
        self.stop()

        path = str(full_path)
        if not os.path.exists(path):
            logger.error("播放失败：找不到音效文件 %s", path)
            return

        flags = winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT
        try:
            winsound.PlaySound(path, flags)
        except Exception as e:
            logger.error("播放失败：无法播放 %s（%s）", path, e)
