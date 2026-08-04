# app/models/params.py
from dataclasses import dataclass, field

# Start 时复制进 PieceCounter / WeightStabilizer（快照，不持有引用）。
# 运行中 UI 修改仅在下一次 Start 生效。
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

# 每帧稳定读数时从共享 Params 实时读取（CounterService）。不持久化。
LIVE_FIELDS = frozenset({"target_pieces"})


@dataclass
class Params:
    """纯数据对象 — 全部应用参数，无 I/O，无 Qt。

     生效规则：
    - START_SYNC_FIELDS：Start 时复制进算法
    - LIVE_FIELDS：每帧从本共享实例读取
    - 其余字段：进程启动加载 / 经 ConfigService 持久化
    """

    # [parameters] — START_SYNC（target_pieces 除外 → LIVE）
    initial_min_weight: float = 0.5
    tolerance_percent: float = 20.0
    stability_threshold: float = 0.02
    max_batch_pieces: int = 1
    initial_single_pieces: int = 5
    target_pieces: int = 100  # LIVE，不持久化
    decimal_places: int = 2

    # [stability] — WeightStabilizer 构造时固定（threshold 属 START_SYNC）
    stability_short_win: int = 5
    stability_long_win: int = 10
    stability_stable_count: int = 3
    stability_unlock_confirm: int = 2
    stability_unlock_factor: float = 2.5

    # [counting] — PieceCounter 构造时复制
    dynamic_weight_ratio: float = 0.5
    initial_min_ratio: float = 0.3
    jump_threshold_ratio: float = 0.5
    jump_confirm_times: int = 2
    early_learn_pieces: int = 5
    ema_alpha_min: float = 0.05
    ema_alpha_max: float = 0.30
    count_rounding_tolerance: float = 0.2
    abnormal_recover_factor: float = 1.5

    # [serial] — 配置 + UI 可编辑
    timeout_millis: int = 2000
    port: str = "COM1"
    baud_rate: int = 9600

    # [ui] — UI 布局持久化
    splitter_sizes: list[int] = field(default_factory=lambda: [400, 600])
