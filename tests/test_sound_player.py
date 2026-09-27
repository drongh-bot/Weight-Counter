# tests/test_sound_player.py
"""SoundPlayer：非 Windows 上没有 winsound，提示音必须静默跳过而不是崩。"""

from app.core import sound_player


class TestSoundPlayerNonWindows:
    def test_all_entry_points_are_noop(self, monkeypatch):
        """强制走非 Windows 分支，三个入口都不该抛异常。"""
        monkeypatch.setattr(sound_player, "_IS_WINDOWS", False)
        player = sound_player.SoundPlayer()

        player.play_error()
        player.play_alert()
        player.stop()  # 非 Windows 上静默返回

    def test_construct_logs_when_disabled(self, monkeypatch, caplog):
        """非 Windows 构造时提示音被禁用，应留一条 warning。"""
        monkeypatch.setattr(sound_player, "_IS_WINDOWS", False)
        with caplog.at_level("WARNING", logger=sound_player.logger.name):
            sound_player.SoundPlayer()
        assert any("提示音已禁用" in m for m in caplog.messages)
