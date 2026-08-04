# app/presentation/status_bar.py
"""状态栏（三标签）：事件入 → BarSnapshot 出。

对外 API 仅 StatusBar。链路绘制与消息锁存为内部实现。

消息显示优先级（高 → 低）：
  强制失败 → 强制完成 → 等待稳定 → 软错误
  → 计数异常 → 达目标 → 无

消息生命周期：
  abnormal   = 每帧由 CounterState 推导
  target     = 边沿锁存；后续加件时清除
  waiting    = 强制校准待稳定期间；稳定路径清除
  force result = 仅当帧
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


class _LinkKind(Enum):
    """内部：绘制解析 + 通讯标签。"""

    OK = auto()
    TIMEOUT = auto()
    PARSE_FAIL = auto()
    FAULT = auto()

    def labels(self) -> tuple[LabelItem, LabelItem]:
        """按链路种类返回（解析标签, 通讯标签）。"""
        if self is _LinkKind.OK:
            return (
                LabelItem(text="解析正常", style=Styles.GREEN),
                LabelItem(text="通讯正常", style=Styles.GREEN),
            )
        if self is _LinkKind.PARSE_FAIL:
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
        """初始化链路与消息锁存状态。"""
        self._link = _LinkKind.OK
        self._state = CounterState.ZERO
        self._hold_target = False
        self._waiting = False
        self._error: str | None = None

    def reset(self) -> BarSnapshot:
        """重置全部内部状态并返回空闲快照。"""
        self._link = _LinkKind.OK
        self._state = CounterState.ZERO
        self._hold_target = False
        self._waiting = False
        self._error = None
        return self.snapshot()

    def on_timeout(self) -> BarSnapshot:
        """串口超时：链路切到等待态。"""
        self._link = _LinkKind.TIMEOUT
        return self.snapshot()

    def on_parse_fail(self) -> BarSnapshot:
        """重量解析失败：解析标签标红。"""
        self._link = _LinkKind.PARSE_FAIL
        return self.snapshot()

    def on_force_waiting(self) -> BarSnapshot:
        """强制校准已挂起，等待稳定重量。"""
        self._link = _LinkKind.OK
        self._waiting = True
        return self.snapshot()

    def on_serial_error(self, msg: str) -> BarSnapshot:
        """串口故障：链路故障 + 软错误消息。"""
        self._link = _LinkKind.FAULT
        self._error = msg
        return self.snapshot()

    def on_csv_error(self, msg: str) -> BarSnapshot:
        """CSV 写入失败：仅更新软错误消息。"""
        self._error = msg
        return self.snapshot()

    def on_start_failed(self, msg: str) -> BarSnapshot:
        """Start 打开串口失败。"""
        self._link = _LinkKind.FAULT
        self._error = msg
        return self.snapshot()

    def on_stable_frame(
        self,
        *,
        state: CounterState,
        target_reached: bool,
        piece_added: bool,
        force_done: bool = False,
        force_failed: bool = False,
    ) -> BarSnapshot:
        """稳定帧：更新链路/状态并解析消息优先级。"""
        self._link = _LinkKind.OK
        self._state = state
        self._error = None
        self._waiting = False
        if target_reached:
            self._hold_target = True
        if piece_added and self._hold_target and not target_reached:
            self._hold_target = False
        return self.snapshot(force_done=force_done, force_failed=force_failed)

    def snapshot(
        self, *, force_done: bool = False, force_failed: bool = False
    ) -> BarSnapshot:
        """按当前锁存状态生成三标签快照。"""
        parse, comm = self._link.labels()
        text, info = self._resolve_message(
            force_done=force_done, force_failed=force_failed
        )
        return BarSnapshot(
            parse=parse,
            comm=comm,
            message=_message_label(text, info=info),
        )

    def _resolve_message(
        self, *, force_done: bool, force_failed: bool
    ) -> tuple[str, bool]:
        """按优先级解析消息文案；返回 (文本, 是否信息色)。"""
        if force_failed:
            return MSG_FORCE_FAIL, False
        if force_done:
            return MSG_FORCE_DONE, True
        if self._waiting:
            return MSG_WAIT_STABLE, True
        if self._error is not None:
            return self._error, False
        if self._state == CounterState.ABNORMAL:
            return MSG_ABNORMAL, True
        if self._hold_target:
            return MSG_TARGET, True
        return MSG_NONE, False
