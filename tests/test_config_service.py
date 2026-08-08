from pathlib import Path

import pytest

from app.models.params import Params
from app.services.config_service import ConfigService


class TestParamsClamp:
    def test_clamps_bad_stability_and_batch(self):
        p = Params(
            stability_long_win=1,
            stability_short_win=0,
            max_batch_pieces=0,
            initial_min_weight=-1,
        )
        assert p.stability_long_win == 2
        assert p.stability_short_win == 1
        assert p.max_batch_pieces == 1
        assert p.initial_min_weight == 0.5

    def test_load_clamps_from_toml(self, tmp_path: Path):
        path = tmp_path / "config.toml"
        path.write_text(
            "[stability]\nstability_long_win = 1\n"
            "[parameters]\nmax_batch_pieces = 0\n",
            encoding="utf-8",
        )
        params = ConfigService().load(path)
        assert params.stability_long_win == 2
        assert params.max_batch_pieces == 1


class TestConfigService:
    def test_load_initial_min_weight(self, tmp_path: Path):
        path = tmp_path / "config.toml"
        path.write_text(
            "[parameters]\ninitial_min_weight = 1.5\n",
            encoding="utf-8",
        )
        params = ConfigService().load(path)
        assert params.initial_min_weight == 1.5

    def test_save_writes_initial_min_weight(self, tmp_path: Path):
        path = tmp_path / "config.toml"
        params = ConfigService().load(path)
        params.initial_min_weight = 0.8
        ConfigService().save(params, path)
        text = path.read_text(encoding="utf-8")
        assert "initial_min_weight" in text
        assert "initial_mini_weight" not in text

    def test_target_pieces_not_persisted(self):
        assert "target_pieces" not in ConfigService.persisted_keys()

    def test_save_omits_target_pieces(self, tmp_path: Path):
        path = tmp_path / "config.toml"
        params = ConfigService().load(path)
        params.target_pieces = 42
        ConfigService().save(params, path)
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

    def test_save_roundtrip(self, tmp_path: Path):
        path = tmp_path / "config.toml"
        params = ConfigService().load(path)
        params.initial_min_weight = 1.25
        ConfigService().save(params, path)
        loaded = ConfigService().load(path)
        assert loaded.initial_min_weight == 1.25

    def test_load_corrupt_toml_raises(self, tmp_path: Path):
        path = tmp_path / "config.toml"
        path.write_text("{{{{not toml", encoding="utf-8")
        with pytest.raises(Exception):
            ConfigService().load(path)
