# app/services/config_service.py
import logging
import threading
from dataclasses import asdict
from pathlib import Path

import toml

from app.models.params import Params

logger = logging.getLogger(__name__)


class ConfigService:
    """I/O 服务：Params ↔ config.toml 加载与保存。"""

    _SECTION_MAP: dict[str, list[str]] = {
        "parameters": [
            "initial_min_weight", "tolerance_percent", "stability_threshold",
            "max_batch_pieces", "initial_single_pieces", "decimal_places",
        ],
        "stability": [
            "stability_short_win", "stability_long_win", "stability_stable_count",
            "stability_unlock_confirm", "stability_unlock_factor",
        ],
        "counting": [
            "dynamic_weight_ratio", "initial_min_ratio", "jump_threshold_ratio",
            "jump_confirm_times", "early_learn_pieces", "ema_alpha_min",
            "ema_alpha_max", "count_rounding_tolerance", "abnormal_recover_factor",
        ],
        "serial": ["timeout_millis", "port", "baud_rate"],
        "ui": ["splitter_sizes"],
    }

    def __init__(self) -> None:
        self._lock = threading.Lock()

    @classmethod
    def persisted_keys(cls) -> frozenset[str]:
        """返回会写入 config.toml 的字段名集合。"""
        return frozenset(k for keys in cls._SECTION_MAP.values() for k in keys)

    def load(self, path: Path) -> Params:
        """加载 config.toml，缺失项用 Params 默认值填充。"""
        with self._lock:
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    raw: dict = toml.load(f)
            else:
                raw = {}

        flat: dict = {}
        for section, keys in self._SECTION_MAP.items():
            section_data = raw.get(section, {})
            for key in keys:
                if key in section_data:
                    flat[key] = section_data[key]

        return Params(**flat)

    def save(self, params: Params, path: Path) -> None:
        """将 Params 持久化到 config.toml。"""
        data = asdict(params)
        toml_data: dict = {}
        for section, keys in self._SECTION_MAP.items():
            toml_data[section] = {key: data[key] for key in keys}

        with self._lock:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    toml.dump(toml_data, f)
            except Exception as e:
                raise RuntimeError(f"保存配置失败: {e}") from e
