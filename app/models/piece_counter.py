# app/models/piece_counter.py
from app.models.counter_state import CounterState
from app.models.params import FixedParams, Params, StartParams
from app.models.thresholds import Thresholds
from app.models.tolerance import Tolerance
from app.models.weight_learner import WeightLearner


class PieceCounter:
    """计件 FSM。持有算法参数的副本 — 不引用共享 Params。"""

    def __init__(self, params: Params | None = None) -> None:
        """按 Params 的三组参数初始化算法。"""
        if params is None:
            params = Params()
        self._copy_start_fields(params.start)
        self._build_helpers(params.start, params.fixed)
        self.reset()

    def _copy_start_fields(self, start: StartParams) -> None:
        """拷贝 Start 组的标量字段，非法值一律用默认值顶上。

        公差百分比不在此列 —— 它归 ``Tolerance.set_percent`` 守卫。
        构造和点 Start 都走这里，所以**每个字段**的守卫只写一次。
        守卫不能省：值可能来自手改的 config.toml，界面控件的 min/max 管不到它。
        """
        default = StartParams()

        self.initial_single_pieces = (
            start.initial_single_pieces
            if start.initial_single_pieces > 0
            else default.initial_single_pieces
        )
        self.max_batch_pieces = (
            start.max_batch_pieces
            if start.max_batch_pieces > 0
            else default.max_batch_pieces
        )
        # tolerance_percent 不在这里：它归 Tolerance 管（见 set_percent 的守卫）
        self.decimal_places = (
            start.decimal_places
            if start.decimal_places >= 0
            else default.decimal_places
        )
        self.stability_threshold = (
            start.stability_threshold
            if start.stability_threshold > 0
            else default.stability_threshold
        )

    def _min_tol(self) -> float:
        """由小数位与稳定阈值推导最小公差。"""
        resolution = 10 ** (-self.decimal_places)
        return max(resolution * 2, self.stability_threshold * 2)

    def _build_helpers(self, start: StartParams, fixed: FixedParams) -> None:
        """用 Start / Fixed 两组参数创建 Tolerance / WeightLearner / Thresholds。

        其中 fixed 的字段只在程序启动时读一次，改 config.toml 要重启才生效。
        """
        self.count_rounding_tolerance = fixed.count_rounding_tolerance
        self.abnormal_recover_factor = fixed.abnormal_recover_factor

        self.tolerance = Tolerance(
            min_tol=self._min_tol(),
            tolerance_percent=StartParams().tolerance_percent,  # 默认打底
        )
        self.tolerance.set_percent(
            start.tolerance_percent
        )  # 守卫覆盖，与点 Start 同一处
        self.learner = WeightLearner(
            jump_threshold_ratio=fixed.jump_threshold_ratio,
            jump_confirm_times=fixed.jump_confirm_times,
            early_learn_pieces=fixed.early_learn_pieces,
            ema_alpha_min=fixed.ema_alpha_min,
            ema_alpha_max=fixed.ema_alpha_max,
        )

        # initial_min_weight 必须 > 0；手改 config.toml 给了负值/零就退回默认
        min_weight = start.initial_min_weight
        if min_weight <= 0:
            min_weight = StartParams().initial_min_weight
        self.thresholds = Thresholds(
            initial_min_weight=min_weight,
            dynamic_weight_ratio=fixed.dynamic_weight_ratio,
            initial_min_ratio=fixed.initial_min_ratio,
        )

    def apply_start_params(self, start: StartParams) -> None:
        """点 Start：拷 Start 组字段（与构造同一套守卫）+ 更新阈值 + 重算 min_tol。

        拷贝值不跟着界面一直变；跑起来中途改这些字段要再点 Start。
        """
        self._copy_start_fields(start)
        self.tolerance.set_percent(start.tolerance_percent)  # 与构造同一处守卫
        if start.initial_min_weight > 0:
            self.thresholds.initial_min_weight = start.initial_min_weight
        self._recalc_min_tol()

    def reset(self) -> None:
        """清空件重列表与状态，回到 ZERO。"""
        self.piece_weights: list[float] = []
        self.baseline_weight = 0.0
        self.last_stable_weight = 0.0
        self.delta_weight = 0.0
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
        # 抖动过滤：还在异常态就不管；否则离上次稳定值不到最小公差的，
        # 当作秤在原地微抖，刷一下 last_stable_weight 就跳过（不当成加/减件）
        if (
            self.state != CounterState.ABNORMAL
            and abs(stable_weight - self.last_stable_weight) < self.tolerance.min_tol
        ):
            self.last_stable_weight = stable_weight
            return

        if self._reset_if_below_min_weight(stable_weight):
            return

        self._update_delta_weight(stable_weight)

        if self.state == CounterState.ZERO:
            self._handle_zero(stable_weight)
        elif self.state == CounterState.NORMAL:
            self._handle_normal(stable_weight)
        elif self.state == CounterState.ABNORMAL:
            self._handle_abnormal(stable_weight)

    def _handle_zero(self, stable_weight: float) -> None:
        """ZERO 态：重量差足够大则作为首件入秤（过轻已在全局守卫处理）。"""
        if abs(self.delta_weight) >= self.thresholds.initial_min_weight:
            self._add_pieces(1, self.delta_weight, stable_weight)
            self.state = CounterState.NORMAL

    def _handle_normal(self, stable_weight: float) -> None:
        """NORMAL 态：匹配加/减件或转入 ABNORMAL。"""
        if abs(self.delta_weight) < self.thresholds.dynamic_min_weight(self.avg_weight):
            self.last_stable_weight = stable_weight
            return

        max_match_pieces = (
            1
            if self.total_pieces < self.initial_single_pieces
            else self.max_batch_pieces
        )

        n = self._try_match_piece_count(self.delta_weight, max_match_pieces)

        if n is not None:
            if self.delta_weight > 0:
                self._add_pieces(n, self.delta_weight, stable_weight)
            else:
                n_remove = min(n, self.total_pieces)
                if n_remove > 0:
                    self._remove_pieces(n_remove, stable_weight)
        else:
            self.state = CounterState.ABNORMAL
            self.abnormal_high = self.delta_weight > 0
            self.abnormal_low = self.delta_weight < 0
            self.abnormal_extreme = stable_weight

    def _handle_abnormal(self, stable_weight: float) -> None:
        """ABNORMAL 态：跟踪锚点，满足恢复条件则退出异常。"""
        self.delta_weight = stable_weight - self.baseline_weight

        # ① 偏差方向变了 → 重置极值锚点（下面几步继续走，不 return）
        if self.delta_weight > 0 and not self.abnormal_high:
            self.abnormal_high = True
            self.abnormal_low = False
            self.abnormal_extreme = stable_weight
        elif self.delta_weight < 0 and not self.abnormal_low:
            self.abnormal_low = True
            self.abnormal_high = False
            self.abnormal_extreme = stable_weight

        # ② 还在往更极端走 → 刷新极值，这一帧不判恢复
        if self.abnormal_high and stable_weight > self.abnormal_extreme:
            self.abnormal_extreme = stable_weight
            return

        if self.abnormal_low and stable_weight < self.abnormal_extreme:
            self.abnormal_extreme = stable_weight
            return

        # ③ 偏差仍在恢复范围外 → 继续等
        if (
            abs(self.delta_weight)
            > self._recover_limit() * self.abnormal_recover_factor
        ):
            return

        # ④ 已回到恢复范围 → 收工，回 NORMAL
        self._reset_baseline(stable_weight)

    def _recover_limit(self) -> float:
        """异常恢复的允许偏差上限（avg×% 与 min_tol 取大）。

        它是本状态机的退出条件，不是计件公差的度量 —— 所以留在这里，
        两个参数取自 ``tolerance``。注意 avg<=0 时仍返回 min_tol（保证异常能恢复），
        这与 ``tolerance.band(0)`` 返回 0 是**有意不同**的。
        """
        if self.avg_weight <= 0:
            return self.tolerance.min_tol
        return max(
            self.avg_weight * (self.tolerance.tolerance_percent / 100.0),
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

    def _update_delta_weight(self, stable_weight: float) -> None:
        """更新相对基准的重量差。"""
        self.delta_weight = stable_weight - self.baseline_weight

    def _try_match_piece_count(self, delta_weight: float, limit: int) -> int | None:
        """尝试把重量差匹配为 1..limit 件；失败返回 None。"""
        if self.avg_weight <= 0:
            return None

        n_est = abs(delta_weight) / self.avg_weight
        n = round(n_est)

        if not (1 <= n <= limit):
            return None

        if abs(n_est - n) > self.count_rounding_tolerance:
            return None

        if not self.tolerance.is_within_tolerance(
            abs(delta_weight), n, self.avg_weight
        ):
            return None

        return n

    def _add_pieces(
        self, count: int, delta_weight: float, stable_weight: float
    ) -> None:
        """接受加件：写入件重、更新均重与基准。"""
        piece_weight = delta_weight / count
        for _ in range(count):
            self.piece_weights.append(piece_weight)

        self.avg_weight = self.learner.update(
            self.avg_weight, piece_weight, count, self.total_pieces
        )
        self.baseline_weight = stable_weight
        self.last_stable_weight = stable_weight

    def _remove_pieces(self, count: int, stable_weight: float) -> None:
        """接受减件：删除末尾 n 件并重算均重。"""
        del self.piece_weights[-count:]
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
