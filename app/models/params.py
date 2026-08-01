# app/models/params.py
from dataclasses import dataclass, field


@dataclass
class Params:
    """Pure data object — all application parameters, no I/O, Qt-free."""

    # [parameters] — runtime mutable
    initial_min_weight: float = 0.5
    tolerance_percent: float = 20.0
    stability_threshold: float = 0.02
    max_batch_pieces: int = 1
    initial_single_pieces: int = 5
    target_pieces: int = 100
    decimal_places: int = 2

    # [stability] — fixed at startup
    stability_short_win: int = 5
    stability_long_win: int = 10
    stability_stable_count: int = 3
    stability_unlock_confirm: int = 2
    stability_unlock_factor: float = 2.5

    # [counting] — fixed at startup
    dynamic_weight_ratio: float = 0.5
    initial_min_ratio: float = 0.3
    jump_threshold_ratio: float = 0.5
    jump_confirm_times: int = 2
    early_learn_pieces: int = 5
    ema_alpha_min: float = 0.05
    ema_alpha_max: float = 0.30
    count_rounding_tolerance: float = 0.2
    abnormal_recover_factor: float = 1.5

    # [serial] — config + UI-editable
    timeout_millis: int = 2000
    port: str = "COM1"
    baud_rate: int = 9600

    # [ui] — UI persistence
    splitter_sizes: list[int] = field(default_factory=lambda: [400, 600])
