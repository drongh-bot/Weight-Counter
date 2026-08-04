# app/models/weight_learner.py


class WeightLearner:
    """EMA 单重学习 + 跳变检测与重置。"""

    def __init__(
        self,
        jump_threshold_ratio: float = 0.5,
        jump_confirm_times: int = 2,
        early_learn_pieces: int = 5,
        ema_alpha_min: float = 0.05,
        ema_alpha_max: float = 0.30,
    ) -> None:
        """初始化跳变检测与 EMA 系数范围。"""
        self.jump_threshold_ratio: float = jump_threshold_ratio
        self.jump_confirm_times: int = jump_confirm_times
        self.early_learn_pieces: int = early_learn_pieces
        self.ema_alpha_min: float = ema_alpha_min
        self.ema_alpha_max: float = ema_alpha_max
        self.jump_count: int = 0

    def reset(self) -> None:
        """清零跳变计数。"""
        self.jump_count = 0

    def update(
        self, avg_weight: float, piece_weight: float, n: int, total_pieces: int
    ) -> float:
        """返回更新后的平均单重。"""
        if total_pieces <= 0:
            return piece_weight

        if total_pieces <= self.early_learn_pieces:
            old_count = total_pieces - n
            if old_count <= 0:
                return piece_weight
            return (avg_weight * old_count + piece_weight * n) / total_pieces

        # 跳变检测
        if avg_weight > 0:
            diff_ratio = abs(piece_weight - avg_weight) / avg_weight
        else:
            diff_ratio = 1.0

        if diff_ratio > self.jump_threshold_ratio:
            self.jump_count += 1
            if self.jump_count >= self.jump_confirm_times:
                # 触发跳变：重置学习
                self.jump_count = 0
                return piece_weight
        else:
            self.jump_count = 0

        # 动态 EMA
        alpha = min(max(diff_ratio, self.ema_alpha_min), self.ema_alpha_max)

        return alpha * piece_weight + (1 - alpha) * avg_weight
