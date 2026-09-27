from pathlib import Path

import pytest

from app.services.config_service import ConfigService


class TestConfigService:
    def test_load_initial_min_weight(self, tmp_path: Path):
        path = tmp_path / "config.toml"
        path.write_text(
            "[parameters]\ninitial_min_weight = 1.5\n",
            encoding="utf-8",
        )
        params = ConfigService(path).load()
        assert params.start.initial_min_weight == 1.5

    def test_save_writes_initial_min_weight(self, tmp_path: Path):
        path = tmp_path / "config.toml"
        svc = ConfigService(path)
        params = svc.load()
        params.start.initial_min_weight = 0.8
        svc.save(params)
        text = path.read_text(encoding="utf-8")
        assert "initial_min_weight" in text
        assert "initial_mini_weight" not in text

    def test_target_pieces_not_persisted(self):
        assert "target_pieces" not in ConfigService.persisted_keys()

    def test_save_omits_target_pieces(self, tmp_path: Path):
        path = tmp_path / "config.toml"
        svc = ConfigService(path)
        params = svc.load()
        params.target_pieces = 42
        svc.save(params)
        text = path.read_text(encoding="utf-8")
        assert "target_pieces" not in text

    def test_ui_count_params_are_persisted(self):
        """界面上要再 Start 才生效的那几项，应能写入配置文件。"""
        persisted = ConfigService.persisted_keys()
        for key in (
            "initial_min_weight",
            "tolerance_percent",
            "stability_threshold",
            "max_batch_pieces",
            "initial_single_pieces",
            "decimal_places",
        ):
            assert key in persisted

    def test_serial_encoding_persisted_and_loaded(self, tmp_path: Path):
        path = tmp_path / "config.toml"
        path.write_text(
            '[serial]\nencoding = "gbk"\n',
            encoding="utf-8",
        )
        params = ConfigService(path).load()
        assert params.fixed.encoding == "gbk"
        assert "encoding" in ConfigService.persisted_keys()

    def test_save_roundtrip(self, tmp_path: Path):
        path = tmp_path / "config.toml"
        svc = ConfigService(path)
        params = svc.load()
        params.start.initial_min_weight = 1.25
        svc.save(params)
        loaded = svc.load()
        assert loaded.start.initial_min_weight == 1.25

    def test_load_corrupt_toml_raises(self, tmp_path: Path):
        path = tmp_path / "config.toml"
        path.write_text("{{{{not toml", encoding="utf-8")
        with pytest.raises(Exception):
            ConfigService(path).load()
