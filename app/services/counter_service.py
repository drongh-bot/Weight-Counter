# app/services/counter_service.py

from app.models.count_result import CountResult
from app.models.params import Params
from app.models.counter_state import CounterState
from app.models.piece_counter import PieceCounter


class CounterService:
    """
    计件业务服务

    职责：
    - 将稳定重量喂入 PieceCounter
    - 检测异常/目标边沿（本帧标志写入 CountResult）
    - 构建 CountResult 统一数据载体
    - 强制校准、重置
    """

    def __init__(self, params: Params) -> None:
        """用共享 Params 构造内部 PieceCounter（内部再拷贝参数）。"""
        self.params = params
        self._piece_counter = PieceCounter(params)

    def apply_start_params(self) -> None:
        """Start 时将共享 Params 的 START_SYNC 字段复制进 PieceCounter。"""
        self._piece_counter.apply_start_params(self.params)

    def _target_crossed(
        self, old_count: int, new_count: int, state: CounterState
    ) -> bool:
        """本帧是否首次跨越目标件数。"""
        target = self.params.target_pieces
        return (
            0 < target
            and old_count < target <= new_count
            and state == CounterState.NORMAL
        )

    def process(self, stable_weight: float) -> CountResult:
        """运行 FSM + 边沿检测；返回 CountResult 快照。"""
        old_count = self._piece_counter.total_pieces
        old_state = self._piece_counter.state

        self._piece_counter.on_stable_weight(stable_weight)

        new_count = self._piece_counter.total_pieces
        new_state = self._piece_counter.state

        return self._build_result(
            added=new_count > old_count,
            abnormal_edge=(
                old_state != CounterState.ABNORMAL
                and new_state == CounterState.ABNORMAL
            ),
            target_edge=self._target_crossed(old_count, new_count, new_state),
        )

    def _build_result(
        self,
        *,
        added: bool = False,
        abnormal_edge: bool = False,
        target_edge: bool = False,
    ) -> CountResult:
        """从 PieceCounter 组装 CountResult（公差带按当前均重现算）。"""
        pc = self._piece_counter
        tol_low, tol_high, _ = pc.tolerance.band(
            pc.avg_weight, pc.tolerance_percent
        )
        return CountResult(
            added=added,
            abnormal_high=pc.abnormal_high,
            abnormal_low=pc.abnormal_low,
            state=pc.state,
            delta=pc.delta,
            avg_weight=pc.avg_weight,
            tolerance_high=tol_high,
            tolerance_low=tol_low,
            total_pieces=pc.total_pieces,
            last_stable_weight=pc.last_stable_weight,
            baseline_weight=pc.baseline_weight,
            piece_weights=list(pc.piece_weights),
            decimal_places=pc.decimal_places,
            abnormal_edge=abnormal_edge,
            target_edge=target_edge,
        )

    def force_calibrate(
        self, stable_weight: float, pieces: int
    ) -> CountResult | None:
        """强制校准。成功返回带边沿标志的快照，失败返回 None。"""
        old_count = self._piece_counter.total_pieces
        if not self._piece_counter.force_calibrate(stable_weight, pieces):
            return None
        new_count = self._piece_counter.total_pieces
        new_state = self._piece_counter.state
        return self._build_result(
            target_edge=self._target_crossed(old_count, new_count, new_state),
        )

    def reset(self) -> None:
        """重置计件器。"""
        self._piece_counter.reset()

    def current_result(self) -> CountResult:
        """返回当前计件快照（不推进 FSM，边沿标志为 False）。"""
        return self._build_result()
