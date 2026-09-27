# app/services/config_service.py
"""读写 config.toml ↔ Params。

加一个配置字段要改**两处**：

1. ``app/models/params.py`` —— 声明字段并归到 ``start`` / ``fixed``
   （归哪组决定何时生效：点 Start，还是要重启程序）
2. 下面的 ``_SECTION_MAP`` —— 决定它落在 toml 哪一节；
   不列进去就是不落盘（``target_pieces`` 就是这样）

两边只靠**字段名**对应，所以改分组不用动 toml，改 toml 结构也不用动分组。
"""

from dataclasses import asdict
from pathlib import Path
from typing import Any, ClassVar

import toml

from app.core.resource_manager import ResourceManager
from app.models.params import Params, params_from


class ConfigService:
    """config.toml 的读写入口：``load`` 读进来，``save`` 写出去。

    路径默认是外部根目录的 ``config.toml``，构造时传别的 path 可覆盖（测试用）。
    ``_SECTION_MAP`` 只回答两件事：文件里有哪些节、每节读写哪些键。
    文件缺项时用 Params 默认值；文件损坏则抛错。
    """

    def __init__(self, path: Path | None = None) -> None:
        """默认读写外部根目录的 config.toml；传 path 隔离到别处。"""
        self._path: Path = (
            path if path is not None else ResourceManager.get_external("config.toml")
        )

    _SECTION_MAP: ClassVar[dict[str, list[str]]] = {
        "parameters": [
            "initial_min_weight",
            "tolerance_percent",
            "stability_threshold",
            "max_batch_pieces",
            "initial_single_pieces",
            "decimal_places",
        ],
        "stability": [
            "stability_short_win",
            "stability_long_win",
            "stability_stable_count",
            "stability_unlock_confirm",
            "stability_unlock_factor",
        ],
        "counting": [
            "dynamic_weight_ratio",
            "initial_min_ratio",
            "jump_threshold_ratio",
            "jump_confirm_times",
            "early_learn_pieces",
            "ema_alpha_min",
            "ema_alpha_max",
            "count_rounding_tolerance",
            "abnormal_recover_factor",
        ],
        "serial": ["timeout_millis", "port", "baud_rate", "encoding"],
        "ui": ["splitter_sizes"],
    }

    @classmethod
    def persisted_keys(cls) -> frozenset[str]:
        """会写入 config.toml 的字段名（只给测试核对用）。"""
        return frozenset(k for keys in cls._SECTION_MAP.values() for k in keys)

    def load(self) -> Params:
        """读 config.toml → Params；文件不存在就全用默认值。"""
        if not self._path.exists():
            return params_from()

        with self._path.open(encoding="utf-8") as f:
            raw: dict[str, Any] = toml.load(f)

        # 按 _SECTION_MAP 挑键，拍平成一份 dict 再交给 params_from 分组
        picked: dict[str, Any] = {}
        for section, keys in self._SECTION_MAP.items():
            data = raw.get(section)
            # 手改 toml 时某节可能被写成非表（如 serial = "abc"），这种节跳过
            if isinstance(data, dict):
                picked.update({k: data[k] for k in keys if k in data})

        return params_from(**picked)

    def save(self, params: Params) -> None:
        """把 Params 写回 config.toml，只写 ``_SECTION_MAP`` 列到的键。"""
        # 分组只存在于代码里，写文件前先把 start / fixed 拍平成一份
        flat = {**asdict(params.start), **asdict(params.fixed)}
        toml_data = {
            section: {key: flat[key] for key in keys}
            for section, keys in self._SECTION_MAP.items()
        }

        try:
            with self._path.open("w", encoding="utf-8") as f:
                toml.dump(toml_data, f)
        except Exception as e:
            raise RuntimeError(f"保存配置失败: {e}") from e
