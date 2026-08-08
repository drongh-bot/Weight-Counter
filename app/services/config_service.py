# app/services/config_service.py
from dataclasses import asdict
from pathlib import Path
from typing import Any

import toml

from app.models.params import Params


class ConfigService:
    """读写 config.toml ↔ 扁平 Params。

    TOML 按节存放，Params 字段是扁平的；``_SECTION_MAP`` 同时决定：
    - 文件里有哪些节、每节哪些键
    - 哪些字段会落盘（未列入的如 ``target_pieces`` 不读也不写）
    文件缺项时用 Params 默认值。
    """

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

    @classmethod
    def persisted_keys(cls) -> frozenset[str]:
        """会写入 config.toml 的字段名。"""
        return frozenset(k for keys in cls._SECTION_MAP.values() for k in keys)

    def load(self, path: Path) -> Params:
        """加载 config.toml；文件不存在或缺键时用 Params 默认值。文件损坏则抛错。"""
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                raw: dict[str, Any] = toml.load(f)
        else:
            raw = {}
        return self._params_from_toml(raw)

    def save(self, params: Params, path: Path) -> None:
        """只把 ``_SECTION_MAP`` 里的字段写入 config.toml。"""
        toml_data = self._toml_from_params(params)
        try:
            with open(path, "w", encoding="utf-8") as f:
                toml.dump(toml_data, f)
        except Exception as e:
            raise RuntimeError(f"保存配置失败: {e}") from e

    def _params_from_toml(self, raw: dict[str, Any]) -> Params:
        """按 ``_SECTION_MAP`` 从分节 dict 收成 Params（缺键走默认）。"""
        flat: dict[str, Any] = {}
        for section, keys in self._SECTION_MAP.items():
            section_data = raw.get(section, {})
            if not isinstance(section_data, dict):
                continue
            for key in keys:
                if key in section_data:
                    flat[key] = section_data[key]
        return Params(**flat)

    def _toml_from_params(self, params: Params) -> dict[str, dict[str, Any]]:
        """按 ``_SECTION_MAP`` 从 Params 只抽出要落盘的分节。"""
        data = asdict(params)
        return {
            section: {key: data[key] for key in keys}
            for section, keys in self._SECTION_MAP.items()
        }
