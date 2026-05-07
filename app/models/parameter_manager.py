# app/models/parameter_manager.py
from app.core.config_manager import ConfigManager


class ParameterManager:
    """
    Parameter Manager

    All parameter defaults, loading, and saving are driven uniformly
    through the _DEFAULTS dict. To add a new parameter, simply modify
    _DEFAULTS and add a type declaration in __init__.
    - No dependency on UI or Controller
    - Collaborates with ConfigManager to read/write config.toml
    """

    _DEFAULTS: dict[str, float | int] = {
        "initial_mini_weight": 0.5,
        "tolerance_percent": 10.0,
        "stability_threshold": 0.02,
        "max_batch_pieces": 1,
        "initial_single_pieces": 1,
        "force_pieces": 0,
        "target_pieces": 100,
        "decimal_places": 2,
    }

    def __init__(self) -> None:
        defaults = self._DEFAULTS
        self.initial_mini_weight: float = defaults["initial_mini_weight"]
        self.tolerance_percent: float = defaults["tolerance_percent"]
        self.stability_threshold: float = defaults["stability_threshold"]
        self.max_batch_pieces: int = int(defaults["max_batch_pieces"])
        self.initial_single_pieces: int = int(defaults["initial_single_pieces"])
        self.force_pieces: int = int(defaults["force_pieces"])
        self.target_pieces: int = int(defaults["target_pieces"])
        self.decimal_places: int = int(defaults["decimal_places"])

        self.config = ConfigManager()

    # ============================================================
    # Load Parameters
    # ============================================================
    def load(self) -> None:
        try:
            self.config.load()
        except Exception:
            return

        params = self.config.data.get("parameters", {})
        for key in self._DEFAULTS:
            setattr(self, key, params.get(key, self._DEFAULTS[key]))

    # ============================================================
    # Save Parameters
    # ============================================================
    def save(self) -> None:
        try:
            self.config.load()
        except Exception:
            return

        self.config.data.setdefault("parameters", {})
        section = self.config.data["parameters"]
        for key in self._DEFAULTS:
            section[key] = getattr(self, key)

        self.config.save()
