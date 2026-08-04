# app/presentation/status_bar.py
"""状态栏（三标签）：事件入 → BarSnapshot 出。

对外 API 仅 StatusBar。解析/通讯绘制与消息锁存为内部实现。

消息显示优先级（高 → 低）：
  强制失败 → 强制完成 → 等待稳定 → 软错误
  → 计数异常 → 达目标 → 无

消息生命周期：
  abnormal   = 每帧由 CounterState 推导
  target     = 边沿锁存；后续加件时清除
  waiting    = 强制校准待稳定期间；稳定路径清除
  force result = 仅当帧（on_force_*_frame）
  soft error = 直至下一稳定帧；超时/未稳定不清除
"""

from __future__ import annotations

from enum import Enum, auto

from app.models.counter_state import CounterState
from app.presentation.styles import Styles
from app.presentation.view_models import BarSnapshot, LabelItem

# 导出供测试断言文案（非独立公共子系统）
MSG_NONE = "无异常"
MSG_WAIT_STABLE = "等待稳定重量…"
MSG_FORCE_DONE = "强制校准完成"
MSG_FORCE_FAIL = "强制校准失败：重量过轻"
MSG_ABNORMAL = "计数异常：调回基准附近可自动恢复，或点强制校准"
MSG_TARGET = "已达目标件数"


class _ParseCommStatus(Enum):
    """内部：解析 + 通讯两格的显示态。"""

    OK = auto()
    TIMEOUT = auto()
    PARSE_FAIL = auto()
    FAULT = auto()


def _parse_comm_labels(status: _ParseCommStatus) -> tuple[LabelItem, LabelItem]:
    """按解析/通讯显示态返回（解析标签, 通讯标签）。"""
    if status is _ParseCommStatus.OK:
        return (
            LabelItem(text="解析正常", style=Styles.GREEN),
            LabelItem(text="通讯正常", style=Styles.GREEN),
        )
    if status is _ParseCommStatus.PARSE_FAIL:
        return (
            LabelItem(text="解析异常", style=Styles.RED),
            LabelItem(text="通讯正常", style=Styles.GREEN),
        )
    return (
        LabelItem(text="解析等待", style=Styles.GRAY),
        LabelItem(text="通讯等待", style=Styles.GRAY),
    )


def _message_label(text: str, *, info: bool = False) -> LabelItem:
    """组装消息栏 LabelItem；info=True 用灰色，否则红色。"""
    if text and text != MSG_NONE:
        style = Styles.GRAY if info else Styles.RED
    else:
        style = ""
    return LabelItem(text=text or MSG_NONE, style=style)


class StatusBar:
    """持有解析 / 通讯 / 消息三格。调用 on_* 后使用返回的快照。"""

    def __init__(self) -> None:
        """初始化解析/通讯与消息锁存状态。"""
        self._parse_comm = _ParseCommStatus.OK
        self._state = CounterState.ZERO
        self._hold_target = False
        self._waiting = False
        self._error: str | None = None

    def reset(self) -> BarSnapshot:
        """重置全部内部状态并返回空闲快照。"""
        self._parse_comm = _ParseCommStatus.OK
        self._state = CounterState.ZERO
        self._hold_target = False
        self._waiting = False
        self._error = None
        return self.snapshot()

    def on_timeout(self) -> BarSnapshot:
        """串口超时：解析/通讯切到等待态。"""
        self._parse_comm = _ParseCommStatus.TIMEOUT
        return self.snapshot()

    def on_parse_fail(self) -> BarSnapshot:
        """重量解析失败：解析标签标红。"""
        self._parse_comm = _ParseCommStatus.PARSE_FAIL
        return self.snapshot()

    def on_force_waiting(self) -> BarSnapshot:
        """强制校准已挂起，等待稳定重量。"""
        self._parse_comm = _ParseCommStatus.OK
        self._waiting = True
        return self.snapshot()

    def on_serial_error(self, msg: str) -> BarSnapshot:
        """串口故障：解析/通讯故障态 + 软错误消息。"""
        self._parse_comm = _ParseCommStatus.FAULT
        self._error = msg
        return self.snapshot()

    def on_csv_error(self, msg: str) -> BarSnapshot:
        """CSV 写入失败：仅更新软错误消息。"""
        self._error = msg
        return self.snapshot()

    def on_start_failed(self, msg: str) -> BarSnapshot:
        """Start 打开串口失败。"""
        self._parse_comm = _ParseCommStatus.FAULT
        self._error = msg
        return self.snapshot()

    def on_stable_frame(
        self,
        *,
        state: CounterState,
        target_reached: bool,
        piece_added: bool,
    ) -> BarSnapshot:
        """普通稳定帧：更新锁存，按优先级出消息（无强制结果）。"""
        self._apply_stable_latches(
            state=state,
            target_reached=target_reached,
            piece_added=piece_added,
        )
        return self.snapshot()

    def on_force_done_frame(
        self,
        *,
        state: CounterState,
        target_reached: bool,
        piece_added: bool,
    ) -> BarSnapshot:
        """强制校准成功当帧：更新锁存，消息为完成。"""
        self._apply_stable_latches(
            state=state,
            target_reached=target_reached,
            piece_added=piece_added,
        )
        return self._snapshot_with_message(MSG_FORCE_DONE, info=True)

    def on_force_fail_frame(
        self,
        *,
        state: CounterState,
        target_reached: bool,
        piece_added: bool,
    ) -> BarSnapshot:
        """强制校准失败当帧：更新锁存，消息为失败。"""
        self._apply_stable_latches(
            state=state,
            target_reached=target_reached,
            piece_added=piece_added,
        )
        return self._snapshot_with_message(MSG_FORCE_FAIL, info=False)

    def snapshot(self) -> BarSnapshot:
        """按当前锁存状态生成三标签快照（不含当帧强制结果）。"""
        parse, comm = _parse_comm_labels(self._parse_comm)
        text, info = self._resolve_message()
        return BarSnapshot(
            parse=parse,
            comm=comm,
            message=_message_label(text, info=info),
        )

    def _apply_stable_latches(
        self,
        *,
        state: CounterState,
        target_reached: bool,
        piece_added: bool,
    ) -> None:
        """稳定路径共用：解析/通讯 OK、清等待/软错误、更新状态与目标锁存。"""
        self._parse_comm = _ParseCommStatus.OK
        self._state = state
        self._error = None
        self._waiting = False
        if target_reached:
            self._hold_target = True
        if piece_added and self._hold_target and not target_reached:
            self._hold_target = False

    def _snapshot_with_message(self, text: str, *, info: bool) -> BarSnapshot:
        """组装快照，消息固定为给定文案（当帧强制结果用）。"""
        parse, comm = _parse_comm_labels(self._parse_comm)
        return BarSnapshot(
            parse=parse,
            comm=comm,
            message=_message_label(text, info=info),
        )

    def _resolve_message(self) -> tuple[str, bool]:
        """按锁存优先级解析消息文案；返回 (文本, 是否信息色)。"""
        if self._waiting:
            return MSG_WAIT_STABLE, True
        if self._error is not None:
            return self._error, False
        if self._state == CounterState.ABNORMAL:
            return MSG_ABNORMAL, True
        if self._hold_target:
            return MSG_TARGET, True
        return MSG_NONE, False
