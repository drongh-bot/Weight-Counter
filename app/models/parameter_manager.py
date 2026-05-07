# app/models/parameter_manager.py
import logging

from app.core.config_manager import ConfigManager

logger = logging.getLogger(__name__)


class ParameterManager:
    """
    Parameter Manager

    All parameter defaults, loading, and saving are driven uniformly
    through the _DEFAULTS dict. To add a new parameter, simply modify
    _DEFAULTS and add a type declaration in __init__.
    - No dependency on UI or Controller
    - Collaborates with ConfigManager to read/write config.toml
    """

    _DEFAULTS: dict[str, dict[str, float | int]] = {
        "parameters": {
            "initial_mini_weight": 0.5,
            "tolerance_percent": 10.0,
            "stability_threshold": 0.02,
            "max_batch_pieces": 1,
            "initial_single_pieces": 1,
            "force_pieces": 0,
            "target_pieces": 100,
            "decimal_places": 2,
        },
        "stability": {
            "short_win": 4,
            "long_win": 8,
            "stable_count": 3,
            "unlock_confirm": 2,
            "unlock_factor": 2.5,
        },
        "counting": {
            "dynamic_weight_ratio": 0.5,
            "initial_min_ratio": 0.3,
            "jump_threshold_ratio": 0.5,
            "jump_confirm_times": 2,
            "early_learn_pieces": 5,
            "ema_alpha_min": 0.05,
            "ema_alpha_max": 0.30,
            "count_rounding_tolerance": 0.2,
            "abnormal_recover_factor": 1.5,
        },
        "serial": {
            "timeout_millis": 2000,
        },
    }

    def __init__(self) -> None:
        self.config = ConfigManager()
        p = self._DEFAULTS["parameters"]
        s = self._DEFAULTS["stability"]
        c = self._DEFAULTS["counting"]
        r = self._DEFAULTS["serial"]
        self.initial_mini_weight: float = p["initial_mini_weight"]
        self.tolerance_percent: float = p["tolerance_percent"]
        self.stability_threshold: float = p["stability_threshold"]
        self.max_batch_pieces: int = int(p["max_batch_pieces"])
        self.initial_single_pieces: int = int(p["initial_single_pieces"])
        self.force_pieces: int = int(p["force_pieces"])
        self.target_pieces: int = int(p["target_pieces"])
        self.decimal_places: int = int(p["decimal_places"])
        self.stability_short_win: int = int(s["short_win"])
        self.stability_long_win: int = int(s["long_win"])
        self.stability_stable_count: int = int(s["stable_count"])
        self.stability_unlock_confirm: int = int(s["unlock_confirm"])
        self.stability_unlock_factor: float = s["unlock_factor"]
        self.dynamic_weight_ratio: float = c["dynamic_weight_ratio"]
        self.initial_min_ratio: float = c["initial_min_ratio"]
        self.jump_threshold_ratio: float = c["jump_threshold_ratio"]
        self.jump_confirm_times: int = int(c["jump_confirm_times"])
        self.early_learn_pieces: int = int(c["early_learn_pieces"])
        self.ema_alpha_min: float = c["ema_alpha_min"]
        self.ema_alpha_max: float = c["ema_alpha_max"]
        self.count_rounding_tolerance: float = c["count_rounding_tolerance"]
        self.abnormal_recover_factor: float = c["abnormal_recover_factor"]
        self.serial_timeout_millis: int = int(r["timeout_millis"])

    # ============================================================
    # Load Parameters
    # ============================================================
    def load(self) -> None:
        try:
            self.config.load()
        except Exception as e:
            logger.error("加载配置失败: %s", e)
            return

        for section, defaults in self._DEFAULTS.items():
            section_data = self.config.data.get(section, {})
            for key, default in defaults.items():
                setattr(self, key, section_data.get(key, default))

    # ============================================================
    # Save Parameters
    # ============================================================
    def save(self) -> None:
        try:
            self.config.load()
        except Exception as e:
            logger.error("保存配置失败: %s", e)
            return

        for section, defaults in self._DEFAULTS.items():
            self.config.data.setdefault(section, {})
            sec = self.config.data[section]
            for key in defaults:
                sec[key] = getattr(self, key)

        self.config.save()
