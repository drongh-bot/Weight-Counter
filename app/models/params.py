# app/models/params.py
from dataclasses import dataclass, field


@dataclass
class Params:
    """整机参数（串口、公差、目标件数、窗口布局等）。

    界面可调参数怎么生效，见各字段旁注释；其余多在开机加载 / 退出保存。
    """

    # —— 计件界面可调 ——
    # 下面几项：点 Start 时拷进算法；跑起来以后改了要再按 Start 才生效
    initial_min_weight: float = 0.5
    tolerance_percent: float = 20.0
    stability_threshold: float = 0.02
    max_batch_pieces: int = 1
    initial_single_pieces: int = 5
    decimal_places: int = 2
    # 目标件数：界面改了立刻算，也不写入配置文件
    target_pieces: int = 100

    # 稳重窗口（创建稳重器时固定；稳定阈值见上面，要再 Start）
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
