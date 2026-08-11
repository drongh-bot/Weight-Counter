# app/services/counter_service.py

from app.models.count_snapshot import CountFrame, CountSnapshot
from app.models.params import Params
from app.models.counter_state import CounterState
from app.models.piece_counter import PieceCounter


class CounterService:
    """对外的计件入口：喂入稳住的重量，得到件数、是否异常、是否刚达目标等。"""

    def __init__(self, params: Params) -> None:
        """用当前参数建好内部计件器。"""
        self.params = params
        self._piece_counter = PieceCounter(params)

    def apply_start_params(self) -> None:
        """点 Start 时：把共享 Params 的计件相关参数拷进算法（中途改了要再 Start）。"""
        self._piece_counter.apply_start_params(self.params)

    def _target_crossed(
        self, old_count: int, new_count: int, state: CounterState
    ) -> bool:
        """这一次计件是否刚从「未达目标」变成「达到或超过目标件数」。"""
        target = self.params.target_pieces
        return (
            0 < target
            and old_count < target <= new_count
            and state == CounterState.NORMAL
        )

    def process(self, stable_weight: float) -> CountFrame:
        """用稳住的重量做一次正常计件，返回最新件数以及「刚发生了什么」（加件/异常/达目标）。"""
        old_count = self._piece_counter.total_pieces
        old_state = self._piece_counter.state

        self._piece_counter.on_stable_weight(stable_weight)

        new_count = self._piece_counter.total_pieces
        new_state = self._piece_counter.state

        return self._build_frame(
            piece_added=new_count > old_count,
            abnormal_edge=(
                old_state != CounterState.ABNORMAL
                and new_state == CounterState.ABNORMAL
            ),
            target_edge=self._target_crossed(old_count, new_count, new_state),
        )

    def _build_snapshot(self) -> CountSnapshot:
        """整理当前件数、均重、公差带等，给界面显示用。"""
        pc = self._piece_counter
        tol = pc.tolerance.band(pc.avg_weight, pc.tolerance_percent)
        return CountSnapshot(
            abnormal_high=pc.abnormal_high,
            abnormal_low=pc.abnormal_low,
            state=pc.state,
            delta=pc.delta,
            avg_weight=pc.avg_weight,
            tolerance_high=tol.high,
            tolerance_low=tol.low,
            total_pieces=pc.total_pieces,
            last_stable_weight=pc.last_stable_weight,
            baseline_weight=pc.baseline_weight,
            piece_weights=list(pc.piece_weights),
            decimal_places=pc.decimal_places,
        )

    def _build_frame(
        self,
        *,
        piece_added: bool = False,
        abnormal_edge: bool = False,
        target_edge: bool = False,
    ) -> CountFrame:
        """在当前件数基础上，附上「这一次」是否加件、是否刚进异常、是否刚达目标。"""
        snap = self._build_snapshot()
        return CountFrame(
            abnormal_high=snap.abnormal_high,
            abnormal_low=snap.abnormal_low,
            state=snap.state,
            delta=snap.delta,
            avg_weight=snap.avg_weight,
            tolerance_high=snap.tolerance_high,
            tolerance_low=snap.tolerance_low,
            total_pieces=snap.total_pieces,
            last_stable_weight=snap.last_stable_weight,
            baseline_weight=snap.baseline_weight,
            piece_weights=snap.piece_weights,
            decimal_places=snap.decimal_places,
            piece_added=piece_added,
            abnormal_edge=abnormal_edge,
            target_edge=target_edge,
        )

    def force_calibrate(
        self, stable_weight: float, pieces: int
    ) -> CountFrame | None:
        """按操作员指定的片数重设单重和件数。重量太轻等失败时返回 None。"""
        old_count = self._piece_counter.total_pieces
        if not self._piece_counter.force_calibrate(stable_weight, pieces):
            return None
        new_count = self._piece_counter.total_pieces
        new_state = self._piece_counter.state
        return self._build_frame(
            target_edge=self._target_crossed(old_count, new_count, new_state),
        )

    def reset(self) -> None:
        """件数清零，回到未放第一件的状态。"""
        self._piece_counter.reset()

    @property
    def decimal_places(self) -> int:
        """界面显示重量用的小数位数（以 Start 时为准）。"""
        return self._piece_counter.decimal_places

    def snapshot(self) -> CountSnapshot:
        """只读当前件数等情况，不根据新重量往下计。"""
        return self._build_snapshot()

    def current_frame(self) -> CountFrame:
        """当前状态快照，无边沿（失败路径刷新 UI、不改计件）。"""
        return self._build_frame()
