# app/models/params.py
from dataclasses import dataclass, field

# 点 Start 时拷进计件/稳重算法的参数。跑起来以后在界面上改它们，要再按一次 Start 才生效。
START_SYNC_FIELDS = frozenset(
    {
        "initial_min_weight",
        "tolerance_percent",
        "stability_threshold",
        "max_batch_pieces",
        "initial_single_pieces",
        "decimal_places",
    }
)

# 目标件数：计件过程中随时跟界面走，不用再按 Start；也不写入配置文件。
LIVE_FIELDS = frozenset({"target_pieces"})


@dataclass
class Params:
    """整机参数（串口、公差、目标件数、窗口布局等）。

    怎么生效：
    - START_SYNC_FIELDS：点 Start 时拷进算法
    - LIVE_FIELDS（目前是目标件数）：计件时直接读这里的最新值
    - 其余：开机从配置文件加载，退出时可保存
    """

    # 计件界面可调（多数要再 Start；目标件数除外）
    initial_min_weight: float = 0.5
    tolerance_percent: float = 20.0
    stability_threshold: float = 0.02
    max_batch_pieces: int = 1
    initial_single_pieces: int = 5
    target_pieces: int = 100  # 随时生效，不存盘
    decimal_places: int = 2

    # 稳重窗口（多数在创建稳重器时固定；稳定阈值见上面 START_SYNC）
    stability_short_win: int = 5
    stability_long_win: int = 10
    stability_stable_count: int = 3
    stability_unlock_confirm: int = 2
    stability_unlock_factor: float = 2.5

    # 计件算法细节（创建时写入计件器）
    dynamic_weight_ratio: float = 0.5
    initial_min_ratio: float = 0.3
    jump_threshold_ratio: float = 0.5
    jump_confirm_times: int = 2
    early_learn_pieces: int = 5
    ema_alpha_min: float = 0.05
    ema_alpha_max: float = 0.30
    count_rounding_tolerance: float = 0.2
    abnormal_recover_factor: float = 1.5

    # 串口
    timeout_millis: int = 2000
    port: str = "COM1"
    baud_rate: int = 9600

    # 界面分割条位置
    splitter_sizes: list[int] = field(default_factory=lambda: [400, 600])
