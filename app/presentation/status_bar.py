# app/presentation/status_bar.py
"""界面底部三格提示：解析是否正常、秤是否连上、当前业务消息。

谁用：MainController 在超时、解析失败、计件变化、强制校准等时机调用 on_*，
把返回值交给界面刷新。

消息谁优先（高 → 低）：
  强制校准失败 → 强制校准完成 → 等待重量稳定 → 串口/CSV 报错
  → 计数异常 → 已达目标件数 → 无异常

消息要显示多久：
  - 计数异常：秤还处在异常就一直显示
  - 已达目标：一直显示，直到之后又加了件
  - 等待稳定：点了强制校准、重量还没稳住时显示；稳住后消失
  - 强制校准成功/失败：只闪一下（当次刷新）
  - 串口/CSV 报错：一直显示到下次重量稳住
"""

from enum import Enum, auto

from app.models.counter_state import CounterState
from app.presentation.view_models import BarSnapshot, LabelItem, Styles

# 供测试核对文案
MSG_NONE = "无异常"
MSG_WAIT_STABLE = "等待稳定重量…"
MSG_FORCE_DONE = "强制校准完成"
MSG_FORCE_FAIL = "强制校准失败：重量过轻"
MSG_ABNORMAL = "计数异常：调回基准附近可自动恢复，或点强制校准"
MSG_TARGET = "已达目标件数"


class _ParseCommStatus(Enum):
    """解析格 + 通讯格当前该显示哪种文案。"""

    OK = auto()
    TIMEOUT = auto()
    PARSE_FAIL = auto()
    FAULT = auto()


def _parse_comm_labels(status: _ParseCommStatus) -> tuple[LabelItem, LabelItem]:
    """根据通讯情况拼出「解析」「通讯」两格文字和颜色。"""
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
    # 超时与串口故障都显示「等待」；具体原因由消息格展示
    return (
        LabelItem(text="解析等待", style=Styles.GRAY),
        LabelItem(text="通讯等待", style=Styles.GRAY),
    )


def _message_label(text: str, *, info: bool = False) -> LabelItem:
    """拼消息格：提示类用灰字，报错类用红字。"""
    if text and text != MSG_NONE:
        style = Styles.GRAY if info else Styles.RED
    else:
        style = ""
    return LabelItem(text=text or MSG_NONE, style=style)


class StatusBar:
    """记住当前该显示什么，每次 on_* 返回三格最新内容给界面。"""

    def __init__(self) -> None:
        self._parse_comm = _ParseCommStatus.OK
        self._state = CounterState.ZERO
        self._hold_target = False
        self._waiting = False
        self._error: str | None = None

    def reset(self) -> BarSnapshot:
        """清空提示，回到开机空闲样子。"""
        self._parse_comm = _ParseCommStatus.OK
        self._state = CounterState.ZERO
        self._hold_target = False
        self._waiting = False
        self._error = None
        return self.bar_snapshot()

    def on_timeout(self) -> BarSnapshot:
        """秤一段时间没回数据。"""
        self._parse_comm = _ParseCommStatus.TIMEOUT
        return self.bar_snapshot()

    def on_parse_fail(self) -> BarSnapshot:
        """串口有数据，但读不出重量数字。"""
        self._parse_comm = _ParseCommStatus.PARSE_FAIL
        return self.bar_snapshot()

    def on_force_waiting_frame(self) -> BarSnapshot:
        """已点强制校准，等秤上重量稳住。"""
        self._parse_comm = _ParseCommStatus.OK
        self._waiting = True
        return self.bar_snapshot()

    def on_serial_error(self, msg: str) -> BarSnapshot:
        """串口出故障（打不开、读写失败等）。"""
        self._parse_comm = _ParseCommStatus.FAULT
        self._error = msg
        return self.bar_snapshot()

    def on_csv_error(self, msg: str) -> BarSnapshot:
        """生产记录写文件失败。"""
        self._error = msg
        return self.bar_snapshot()

    def on_start_failed(self, msg: str) -> BarSnapshot:
        """点 Start 后串口没打开成功。"""
        self._parse_comm = _ParseCommStatus.FAULT
        self._error = msg
        return self.bar_snapshot()

    def on_stable_frame(
        self,
        *,
        state: CounterState,
        target_edge: bool,
        piece_added: bool,
    ) -> BarSnapshot:
        """重量已稳住且走完普通计件：刷新三格（不含强制校准结果提示）。"""
        self._apply_stable_latches(
            state=state,
            target_edge=target_edge,
            piece_added=piece_added,
        )
        return self.bar_snapshot()

    def on_force_done_frame(
        self,
        *,
        state: CounterState,
        target_edge: bool,
        piece_added: bool,
    ) -> BarSnapshot:
        """强制校准成功：三格按最新计件更新，消息显示「强制校准完成」。"""
        self._apply_stable_latches(
            state=state,
            target_edge=target_edge,
            piece_added=piece_added,
        )
        return self._snapshot_with_message(MSG_FORCE_DONE, info=True)

    def on_force_fail_frame(
        self,
        *,
        state: CounterState,
        target_edge: bool,
        piece_added: bool,
    ) -> BarSnapshot:
        """强制校准失败（例如重量过轻）：消息显示失败原因。"""
        self._apply_stable_latches(
            state=state,
            target_edge=target_edge,
            piece_added=piece_added,
        )
        return self._snapshot_with_message(MSG_FORCE_FAIL, info=False)

    def bar_snapshot(self) -> BarSnapshot:
        """按当前记住的状态拼出三格（不含「刚强制校准成功/失败」那种一次性提示）。"""
        text, info = self._resolve_message()
        return self._snapshot_with_message(text, info=info)

    def _apply_stable_latches(
        self,
        *,
        state: CounterState,
        target_edge: bool,
        piece_added: bool,
    ) -> None:
        """重量稳住后的共同更新：通讯恢复正常，清掉等待/报错，并处理「已达目标」提示。"""
        self._parse_comm = _ParseCommStatus.OK
        self._state = state
        self._error = None
        self._waiting = False
        if target_edge:
            self._hold_target = True
        if piece_added and self._hold_target and not target_edge:
            self._hold_target = False

    def _snapshot_with_message(self, text: str, *, info: bool) -> BarSnapshot:
        """拼三格：解析/通讯按当前状态，消息格用传入文案。"""
        parse, comm = _parse_comm_labels(self._parse_comm)
        return BarSnapshot(
            parse=parse,
            comm=comm,
            message=_message_label(text, info=info),
        )

    def _resolve_message(self) -> tuple[str, bool]:
        """按优先级选出当前该显示的消息；第二个返回值 True 表示用灰色提示，False 表示红色报错。"""
        if self._waiting:
            return MSG_WAIT_STABLE, True
        if self._error is not None:
            return self._error, False
        if self._state == CounterState.ABNORMAL:
            return MSG_ABNORMAL, True
        if self._hold_target:
            return MSG_TARGET, True
        return MSG_NONE, False
