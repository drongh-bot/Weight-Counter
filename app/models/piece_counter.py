# app/models/piece_counter.py
from app.models.counter_state import CounterState
from app.models.params import Params
from app.models.thresholds import Thresholds
from app.models.tolerance import Tolerance
from app.models.weight_learner import WeightLearner


class PieceCounter:
    """计件 FSM。持有算法参数的副本 — 不引用共享 Params。"""

    def __init__(self, params: Params | None = None) -> None:
        """从 Params 拷贝算法字段并初始化辅助对象。"""
        p = Params() if params is None else params
        self._load_start_fields(p)
        self._build_helpers(p)
        self.reset()

    def _load_start_fields(self, p: Params) -> None:
        """拷贝 Start 可同步 / 运行期会读的字段。"""
        self.max_batch_pieces = p.max_batch_pieces
        self.initial_single_pieces = p.initial_single_pieces
        self.decimal_places = p.decimal_places
        self.count_rounding_tolerance = p.count_rounding_tolerance
        self.abnormal_recover_factor = p.abnormal_recover_factor
        self.stability_threshold = p.stability_threshold
        self.tolerance_percent = p.tolerance_percent

    def _min_tol(self) -> float:
        """由小数位与稳定阈值推导最小公差。"""
        resolution = 10 ** (-self.decimal_places)
        return max(resolution * 2, self.stability_threshold * 2)

    def _build_helpers(self, p: Params) -> None:
        """用 Params 构造期字段创建 Tolerance / WeightLearner / Thresholds。"""
        self.tolerance = Tolerance(min_tol=self._min_tol())
        self.learner = WeightLearner(
            jump_threshold_ratio=p.jump_threshold_ratio,
            jump_confirm_times=p.jump_confirm_times,
            early_learn_pieces=p.early_learn_pieces,
            ema_alpha_min=p.ema_alpha_min,
            ema_alpha_max=p.ema_alpha_max,
        )
        self.thresholds = Thresholds(
            initial_min_weight=p.initial_min_weight,
            dynamic_weight_ratio=p.dynamic_weight_ratio,
            initial_min_ratio=p.initial_min_ratio,
        )

    def apply_start_params(self, params: Params) -> None:
        """从共享 Params 复制「点 Start 才生效」的那些字段（拷贝值，不跟着界面一直变）。"""
        if params.initial_single_pieces > 0:
            self.initial_single_pieces = params.initial_single_pieces
        if params.max_batch_pieces > 0:
            self.max_batch_pieces = params.max_batch_pieces
        if 0.0 < params.tolerance_percent < 100.0:
            self.tolerance_percent = params.tolerance_percent
        if params.initial_min_weight > 0:
            self.thresholds.initial_min_weight = params.initial_min_weight
        if params.decimal_places >= 0:
            self.decimal_places = params.decimal_places
        if params.stability_threshold > 0:
            self.stability_threshold = params.stability_threshold
        self._recalc_min_tol()

    def reset(self) -> None:
        """清空件重列表与状态，回到 ZERO。"""
        self.piece_weights: list[float] = []
        self.baseline_weight = 0.0
        self.last_stable_weight = 0.0
        self.delta = 0.0
        self.state = CounterState.ZERO
        self.abnormal_high = False
        self.abnormal_low = False
        self.avg_weight = 0.0
        self.abnormal_extreme = 0.0
        self.learner.reset()

    @property
    def total_pieces(self) -> int:
        """当前已计件数。"""
        return len(self.piece_weights)

    def on_stable_weight(self, stable_weight: float) -> None:
        """处理一次稳定重量样本（会改变 FSM 状态）。"""
        if self.state != CounterState.ABNORMAL:
            if abs(stable_weight - self.last_stable_weight) < self.tolerance.min_tol:
                self.last_stable_weight = stable_weight
                return

        if self._reset_if_below_min_weight(stable_weight):
            return

        self._update_delta(stable_weight)

        if self.state == CounterState.ZERO:
            self._handle_zero(stable_weight)
        elif self.state == CounterState.NORMAL:
            self._handle_normal(stable_weight)
        elif self.state == CounterState.ABNORMAL:
            self._handle_abnormal(stable_weight)

    def _handle_zero(self, stable_weight: float) -> None:
        """ZERO 态：delta 足够大则作为首件入秤（过轻已在全局守卫处理）。"""
        if abs(self.delta) >= self.thresholds.initial_min_weight:
            self._add_pieces(1, self.delta, stable_weight)
            self.state = CounterState.NORMAL

    def _handle_normal(self, stable_weight: float) -> None:
        """NORMAL 态：匹配加/减件或转入 ABNORMAL。"""
        if abs(self.delta) < self.thresholds.dynamic_min_weight(self.avg_weight):
            self.last_stable_weight = stable_weight
            return

        limit = (
            1
            if self.total_pieces < self.initial_single_pieces
            else self.max_batch_pieces
        )

        n = self._try_match_piece_count(self.delta, limit)

        if n is not None:
            if self.delta > 0:
                self._add_pieces(n, self.delta, stable_weight)
            else:
                n_remove = min(n, self.total_pieces)
                if n_remove > 0:
                    self._remove_pieces(n_remove, stable_weight)
        else:
            self.state = CounterState.ABNORMAL
            self.abnormal_high = self.delta > 0
            self.abnormal_low = self.delta < 0
            self.abnormal_extreme = stable_weight

    def _handle_abnormal(self, stable_weight: float) -> None:
        """ABNORMAL 态：跟踪锚点，满足恢复条件则退出异常。"""
        current_delta = stable_weight - self.baseline_weight

        if current_delta > 0 and not self.abnormal_high:
            self.abnormal_high = True
            self.abnormal_low = False
            self.abnormal_extreme = stable_weight
        elif current_delta < 0 and not self.abnormal_low:
            self.abnormal_low = True
            self.abnormal_high = False
            self.abnormal_extreme = stable_weight

        if self.abnormal_high and stable_weight > self.abnormal_extreme:
            self.abnormal_extreme = stable_weight
            return

        if self.abnormal_low and stable_weight < self.abnormal_extreme:
            self.abnormal_extreme = stable_weight
            return

        if (
            abs(current_delta)
            > self._recover_limit() * self.abnormal_recover_factor
        ):
            return

        self._reset_baseline(stable_weight)

    def _recover_limit(self) -> float:
        """异常恢复：相对基准允许的绝对偏差上限（avg×% 与 min_tol 取大）。"""
        if self.avg_weight <= 0:
            return self.tolerance.min_tol
        return max(
            self.avg_weight * (self.tolerance_percent / 100.0),
            self.tolerance.min_tol,
        )

    def _reset_baseline(self, stable_weight: float) -> None:
        """将计件锚点重置为 stable_weight 并回到 NORMAL。"""
        self.state = CounterState.NORMAL
        self.abnormal_high = False
        self.abnormal_low = False
        self.abnormal_extreme = 0.0
        self.last_stable_weight = stable_weight
        self.baseline_weight = stable_weight

    def force_calibrate(self, stable_weight: float, force_pieces: int) -> bool:
        """强制校准：按指定片数重设单重与基准。成功返回 True。"""
        if stable_weight < self.thresholds.initial_min_weight or force_pieces <= 0:
            return False

        piece_weight = stable_weight / force_pieces
        self.piece_weights = [piece_weight] * force_pieces

        self.avg_weight = piece_weight
        self._reset_baseline(stable_weight)
        return True

    def _reset_if_below_min_weight(self, stable_weight: float) -> bool:
        """全局守卫：重量低于初始最小重量则 reset 回零并记录空秤基准；返回是否已处理。"""
        if stable_weight < self.thresholds.initial_min_weight:
            self.reset()
            self.baseline_weight = stable_weight
            self.last_stable_weight = stable_weight
            return True
        return False

    def _update_delta(self, stable_weight: float) -> None:
        """更新相对基准的重量差。"""
        self.delta = stable_weight - self.baseline_weight

    def _try_match_piece_count(self, delta: float, limit: int) -> int | None:
        """尝试把 delta 匹配为 1..limit 件；失败返回 None。"""
        if self.avg_weight <= 0:
            return None

        n_est = abs(delta) / self.avg_weight
        n = int(round(n_est))

        if not (1 <= n <= limit):
            return None

        if abs(n_est - n) > self.count_rounding_tolerance:
            return None

        if not self.tolerance.is_within_tolerance(
            abs(delta), n, self.avg_weight, self.tolerance_percent
        ):
            return None

        return n

    def _add_pieces(self, n: int, delta: float, stable_weight: float) -> None:
        """接受加件：写入件重、更新均重与基准。"""
        piece_weight = delta / n
        for _ in range(n):
            self.piece_weights.append(piece_weight)

        self.avg_weight = self.learner.update(
            self.avg_weight, piece_weight, n, self.total_pieces
        )
        self.baseline_weight = stable_weight
        self.last_stable_weight = stable_weight

    def _remove_pieces(self, n: int, stable_weight: float) -> None:
        """接受减件：删除末尾 n 件并重算均重。"""
        del self.piece_weights[-n:]
        if not self.piece_weights:
            # 清空后回到 ZERO，避免 avg=0 的 NORMAL 无法再匹配加件
            self.avg_weight = 0.0
            self.state = CounterState.ZERO
            self.abnormal_high = False
            self.abnormal_low = False
            self.abnormal_extreme = 0.0
            self.learner.reset()
        else:
            self.avg_weight = sum(self.piece_weights) / len(self.piece_weights)
        self.baseline_weight = stable_weight
        self.last_stable_weight = stable_weight

    def _recalc_min_tol(self) -> None:
        """小数位或稳定阈值变化后重算 Tolerance.min_tol（唯一存放处）。"""
        self.tolerance.min_tol = self._min_tol()
