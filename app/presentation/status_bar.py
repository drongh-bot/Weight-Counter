# app/presentation/status_bar.py
"""Status bar (three labels): event in → BarSnapshot out.

Public API is StatusBar only. Link paint and message latches are private.

Message display priority (high → low):
  Force fail → Force done → Force waiting → soft error
  → counting abnormal → target reached → none

Message lifetime:
  abnormal   = derived from CounterState on each snapshot
  target     = latched on edge; cleared on a later piece-add
  waiting    = while force pending & not ready; cleared on stable path
  force result = that frame only
  soft error = until next stable frame; timeout/unstable do not clear
"""

from __future__ import annotations

from enum import Enum, auto

from app.models.counter_state import CounterState
from app.presentation.styles import Styles
from app.presentation.view_models import BarSnapshot, LabelItem

# Exported for tests asserting copy (not a separate public subsystem).
MSG_NONE = "无异常"
MSG_WAIT_STABLE = "等待稳定重量…"
MSG_FORCE_DONE = "强制校准完成"
MSG_FORCE_FAIL = "强制校准失败：重量过轻"
MSG_ABNORMAL = "计数异常：调回基准附近可自动恢复，或点强制校准"
MSG_TARGET = "已达目标件数"


class ForceOutcome(Enum):
    """This-frame force-calibrate result (not latched)."""

    NONE = auto()
    DONE = auto()
    FAIL = auto()


class _LinkKind(Enum):
    """Internal: paints parse + comm labels."""

    OK = auto()
    TIMEOUT = auto()
    PARSE_FAIL = auto()
    FAULT = auto()

    def labels(self) -> tuple[LabelItem, LabelItem]:
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
    if text and text != MSG_NONE:
        style = Styles.GRAY if info else Styles.RED
    else:
        style = ""
    return LabelItem(text=text or MSG_NONE, style=style)


class StatusBar:
    """Owns parse / comm / message. Call on_* then use the returned snapshot."""

    def __init__(self) -> None:
        self._link = _LinkKind.OK
        self._state = CounterState.ZERO
        self._hold_target = False
        self._waiting = False
        self._error: str | None = None

    def reset(self) -> BarSnapshot:
        self._link = _LinkKind.OK
        self._state = CounterState.ZERO
        self._hold_target = False
        self._waiting = False
        self._error = None
        return self.snapshot()

    def on_timeout(self) -> BarSnapshot:
        self._link = _LinkKind.TIMEOUT
        return self.snapshot()

    def on_parse_fail(self) -> BarSnapshot:
        self._link = _LinkKind.PARSE_FAIL
        return self.snapshot()

    def on_force_waiting(self) -> BarSnapshot:
        self._link = _LinkKind.OK
        self._waiting = True
        return self.snapshot()

    def on_serial_error(self, msg: str) -> BarSnapshot:
        self._link = _LinkKind.FAULT
        self._error = msg
        return self.snapshot()

    def on_csv_error(self, msg: str) -> BarSnapshot:
        self._error = msg
        return self.snapshot()

    def on_start_failed(self, msg: str) -> BarSnapshot:
        self._link = _LinkKind.FAULT
        self._error = msg
        return self.snapshot()

    def on_stable_frame(
        self,
        *,
        state: CounterState,
        force: ForceOutcome,
        target_reached: bool,
        piece_added: bool,
    ) -> BarSnapshot:
        self._link = _LinkKind.OK
        self._state = state
        self._error = None
        self._waiting = False
        if target_reached:
            self._hold_target = True
        if piece_added and self._hold_target and not target_reached:
            self._hold_target = False
        return self.snapshot(force=force)

    def snapshot(self, force: ForceOutcome = ForceOutcome.NONE) -> BarSnapshot:
        parse, comm = self._link.labels()
        text, info = self._resolve_message(force)
        return BarSnapshot(
            parse=parse,
            comm=comm,
            message=_message_label(text, info=info),
        )

    def _resolve_message(self, force: ForceOutcome) -> tuple[str, bool]:
        if force is ForceOutcome.FAIL:
            return MSG_FORCE_FAIL, False
        if force is ForceOutcome.DONE:
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
