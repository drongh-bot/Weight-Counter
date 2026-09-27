# app/core/sound_player.py
from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

from app.core.resource_manager import ResourceManager

logger = logging.getLogger(__name__)

# winsound 只在 Windows 上有；其他平台提示音直接跳过，不能让程序起不来
_IS_WINDOWS = sys.platform == "win32"


class SoundPlayer:
    """播放错误/告警 wav。无 Qt、非单例 — 由 main 注入唯一实例。"""

    def __init__(self) -> None:
        """非 Windows 上提示音不可用，启动时说一声，免得静默失效。"""
        if not _IS_WINDOWS:
            logger.warning("当前系统没有 winsound，提示音已禁用")

    def play_error(self) -> None:
        """播放错误提示音。"""
        self._play(ResourceManager.get_resource("app/resources/sounds/error.wav"))

    def play_alert(self) -> None:
        """播放目标达成告警音。"""
        self._play(ResourceManager.get_resource("app/resources/sounds/alert.wav"))

    def stop(self) -> None:
        """停止当前播放。"""
        if not _IS_WINDOWS:
            return
        import winsound

        winsound.PlaySound(None, winsound.SND_PURGE)

    def _play(self, full_path: Path | str) -> None:
        """异步播放一次 wav；非 Windows 没有 winsound，直接跳过。"""
        self.stop()
        if not _IS_WINDOWS:
            return
        import winsound

        path = str(full_path)
        if not os.path.exists(path):
            logger.error("播放失败：找不到音效文件 %s", path)
            return

        flags = winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT
        try:
            winsound.PlaySound(path, flags)
        except Exception as e:
            logger.error("播放失败：无法播放 %s（%s）", path, e)
