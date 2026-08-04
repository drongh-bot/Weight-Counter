from pathlib import Path

from app.models.params import START_SYNC_FIELDS
from app.services.config_service import ConfigService


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

    def test_start_sync_fields_are_persisted(self):
        persisted = ConfigService.persisted_keys()
        assert START_SYNC_FIELDS <= persisted
