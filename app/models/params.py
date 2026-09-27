# app/models/params.py
from dataclasses import dataclass, field, fields
from typing import Any


@dataclass
class StartParams:
    """点 Start 时拷进算法；跑起来以后改了要再按 Start 才生效。"""

    initial_min_weight: float = 0.5
    tolerance_percent: float = 20.0
    stability_threshold: float = 0.02
    max_batch_pieces: int = 1
    initial_single_pieces: int = 5
    decimal_places: int = 2


@dataclass
class FixedParams:
    """程序启动时读入；改 config.toml 后要重启程序才生效。"""

    # 稳重窗口（创建稳重器时固定）
    stability_short_win: int = 5
    stability_long_win: int = 10
    stability_stable_count: int = 3
    stability_unlock_confirm: int = 2
    stability_unlock_factor: float = 2.5

    # 计件算法细节（创建计件器时写入）
    dynamic_weight_ratio: float = 0.5
    initial_min_ratio: float = 0.3
    jump_threshold_ratio: float = 0.5
    jump_confirm_times: int = 2
    early_learn_pieces: int = 5
    ema_alpha_min: float = 0.05
    ema_alpha_max: float = 0.30
    count_rounding_tolerance: float = 0.2
    abnormal_recover_factor: float = 1.5

    # 串口（无界面，直接改 config.toml）
    timeout_millis: int = 2000
    port: str = "COM1"
    baud_rate: int = 9600
    encoding: str = "utf-8"

    # 界面分割条位置
    splitter_sizes: list[int] = field(default_factory=lambda: [400, 600])


@dataclass
class Params:
    """整机参数，按生效时机分组。

    - ``target_pieces``：唯一随时生效的字段（界面改了立刻算），也不写入配置文件
    - ``start``：点 Start 时拷进算法
    - ``fixed``：程序启动时读入，改了要重启
    """

    target_pieces: int = 100
    start: StartParams = field(default_factory=StartParams)
    fixed: FixedParams = field(default_factory=FixedParams)


def pick(flat: dict[str, Any], cls: type) -> dict[str, Any]:
    """从扁平 dict 里挑出属于某个参数组的字段。"""
    names = {f.name for f in fields(cls)}
    return {k: v for k, v in flat.items() if k in names}


def params_from(**kwargs: Any) -> Params:
    """按字段归属自动分组构造 Params（ConfigService 与测试共用）。"""
    return Params(
        target_pieces=kwargs.get("target_pieces", 100),
        start=StartParams(**pick(kwargs, StartParams)),
        fixed=FixedParams(**pick(kwargs, FixedParams)),
    )
