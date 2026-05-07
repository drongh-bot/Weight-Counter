# app/models/parameter_manager.py
import logging
import threading
from typing import Any

import toml

from app.core.resource_manager import ResourceManager

logger = logging.getLogger(__name__)


class ParameterManager:
    """
    Parameter Manager — single source of truth for all configuration.

    All parameter defaults, loading, and saving are driven uniformly
    through the _DEFAULTS dict. To add a new parameter, simply modify
    _DEFAULTS.
    - No dependency on UI or Controller
    - Reads/writes config.toml directly
    """

    _DEFAULTS: dict[str, dict[str, float | int | str]] = {
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
            "port": "COM1",
            "baud_rate": 9600,
            "timeout_millis": 2000,
        },
    }

    def __init__(self) -> None:
        self._data: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()
        p = self._DEFAULTS["parameters"]
        s = self._DEFAULTS["stability"]
        c = self._DEFAULTS["counting"]
        r = self._DEFAULTS["serial"]
        self.initial_mini_weight: float = float(p["initial_mini_weight"])
        self.tolerance_percent: float = float(p["tolerance_percent"])
        self.stability_threshold: float = float(p["stability_threshold"])
        self.max_batch_pieces: int = int(p["max_batch_pieces"])
        self.initial_single_pieces: int = int(p["initial_single_pieces"])
        self.force_pieces: int = int(p["force_pieces"])
        self.target_pieces: int = int(p["target_pieces"])
        self.decimal_places: int = int(p["decimal_places"])
        self.stability_short_win: int = int(s["short_win"])
        self.stability_long_win: int = int(s["long_win"])
        self.stability_stable_count: int = int(s["stable_count"])
        self.stability_unlock_confirm: int = int(s["unlock_confirm"])
        self.stability_unlock_factor: float = float(s["unlock_factor"])
        self.dynamic_weight_ratio: float = float(c["dynamic_weight_ratio"])
        self.initial_min_ratio: float = float(c["initial_min_ratio"])
        self.jump_threshold_ratio: float = float(c["jump_threshold_ratio"])
        self.jump_confirm_times: int = int(c["jump_confirm_times"])
        self.early_learn_pieces: int = int(c["early_learn_pieces"])
        self.ema_alpha_min: float = float(c["ema_alpha_min"])
        self.ema_alpha_max: float = float(c["ema_alpha_max"])
        self.count_rounding_tolerance: float = float(c["count_rounding_tolerance"])
        self.abnormal_recover_factor: float = float(c["abnormal_recover_factor"])
        self.serial_timeout_millis: int = int(r["timeout_millis"])
        self.port: str = str(r["port"])
        self.baud_rate: int = int(r["baud_rate"])

    def set_value(self, section: str, key: str, value: Any) -> None:
        with self._lock:
            if section not in self._data:
                self._data[section] = {}
            self._data[section][key] = value

    def save(self) -> None:
        """Write parameter sections to _data and persist to disk."""
        with self._lock:
            for section, defaults in self._DEFAULTS.items():
                self._data.setdefault(section, {})
                sec = self._data[section]
                for key in defaults:
                    sec[key] = getattr(self, key)

            path = ResourceManager.get_external_root() / "config.toml"
            try:
                with open(path, "w", encoding="utf-8") as f:
                    toml.dump(self._data, f)
            except Exception as e:
                raise RuntimeError(f"保存配置失败: {e}") from e

    def load(self) -> None:
        """Load config.toml and apply values to typed attributes."""
        path = ResourceManager.get_external_root() / "config.toml"
        with self._lock:
            try:
                if path.exists():
                    with open(path, "r", encoding="utf-8") as f:
                        self._data = toml.load(f)
                else:
                    self._data = {}
            except Exception as e:
                logger.error("加载配置失败: %s", e)
                return

            for section, defaults in self._DEFAULTS.items():
                section_data = self._data.get(section, {})
                for key, default in defaults.items():
                    setattr(self, key, type(default)(section_data.get(key, default)))
