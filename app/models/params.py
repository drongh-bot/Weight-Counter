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

    def __post_init__(self) -> None:
        """夹紧明显非法值，避免坏 config 直接打崩稳重/计件。"""
        if self.stability_long_win < 2:
            self.stability_long_win = 2
        if self.stability_short_win < 1:
            self.stability_short_win = 1
        if self.stability_short_win > self.stability_long_win:
            self.stability_short_win = self.stability_long_win
        if self.stability_stable_count < 1:
            self.stability_stable_count = 1
        if self.stability_unlock_confirm < 1:
            self.stability_unlock_confirm = 1
        if self.max_batch_pieces < 1:
            self.max_batch_pieces = 1
        if self.initial_single_pieces < 1:
            self.initial_single_pieces = 1
        if self.jump_confirm_times < 1:
            self.jump_confirm_times = 1
        if self.early_learn_pieces < 1:
            self.early_learn_pieces = 1
        if self.decimal_places < 0:
            self.decimal_places = 0
        if self.initial_min_weight <= 0:
            self.initial_min_weight = 0.5
        if self.stability_threshold <= 0:
            self.stability_threshold = 0.02
        if not (0.0 < self.tolerance_percent < 100.0):
            self.tolerance_percent = 20.0
        if self.target_pieces < 0:
            self.target_pieces = 0
        if self.timeout_millis < 1:
            self.timeout_millis = 2000
