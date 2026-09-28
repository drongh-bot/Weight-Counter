# tests/test_main_window.py
"""MainWindow：装配、参数控件双向绑定、渲染、关闭时保存。

不测 start/强制校准 —— 那两条路会弹 QMessageBox 卡死测试，且需要真实串口。
"""

import pytest

from app.models.counter_state import CounterState
from app.models.params import Params
from app.presentation.view_data import ControlStatus
from app.services.config_service import ConfigService
from app.views.main_window import MainWindow
from tests.conftest import make_count_snapshot


@pytest.fixture
def window(make_controller, tmp_path):
    """造一个完整主窗口；配置写到 tmp_path，不碰真 config.toml。"""
    controller, ui_bridge = make_controller()
    params = Params()
    config = ConfigService(tmp_path / "config.toml")
    win = MainWindow(
        ui_bridge=ui_bridge,
        controller=controller,
        params=params,
        config_service=config,
    )
    yield win, params, config


class TestConstruction:
    def test_builds_and_connects_signals(self, window):
        """构造就把 4 条信号接上 —— 悬空控件引用会在这里直接崩。"""
        win, _, _ = window
        assert win.lblTotalPieces is not None
        assert win.wgtPieceTable is not None
        assert win.wgtPieceChart is not None

    def test_initial_ui_reflects_params(self, window):
        _, params, _ = window
        params.start.decimal_places = 3
        params.target_pieces = 42

        win = window[0]
        win._load_params_to_ui()

        assert win.spnDecimalPlaces.value() == 3
        assert win.spnTargetPieces.value() == 42


class TestParamsBinding:
    def test_controls_write_back_to_params(self, window):
        """控件 → Params.start / Params.target_pieces（写字段，不换子对象）。"""
        win, params, _ = window
        win.dspnTolerancePercent.setValue(11.0)
        win.spnMaxBatchPieces.setValue(3)
        win.spnTargetPieces.setValue(7)

        win._sync_ui_to_params()

        assert params.start.tolerance_percent == 11.0
        assert params.start.max_batch_pieces == 3
        assert params.target_pieces == 7
        assert isinstance(params.start, type(params.start))  # 仍是同一类实例

    def test_shared_start_object_is_not_replaced(self, window):
        """改控件只能改字段，不能整体换掉 params.start —— 否则共享断掉。"""
        win, params, _ = window
        start_before = params.start
        win.dspnTolerancePercent.setValue(12.0)
        win._sync_ui_to_params()
        assert params.start is start_before

    def test_target_pieces_stays_enabled_when_params_locked(self, window):
        """跑起来后 Start 参数要锁，但 target_pieces 随时可改。"""
        win, _, _ = window
        win._on_control_status_changed(
            ControlStatus(start_enabled=False, start_params_enabled=False)
        )

        assert not win.dspnTolerancePercent.isEnabled()  # 锁
        assert win.spnTargetPieces.isEnabled()  # 不锁
        assert not win.btnStart.isEnabled()


class TestSavingAndLoading:
    def test_save_params_writes_config(self, window):
        win, _, config = window
        win.dspnTolerancePercent.setValue(13.0)
        win.spnTargetPieces.setValue(9)

        win._save_params()

        loaded = config.load()
        assert loaded.start.tolerance_percent == 13.0
        assert loaded.target_pieces == 100  # target_pieces 不落盘 → 读回默认值

    def test_close_event_saves_config(self, tmp_path, window):
        """关闭窗口要自动存一次配置 —— 按钮没了，全靠这条兜底。"""
        win, _, _ = window
        config_path = tmp_path / "config.toml"
        assert not config_path.exists()

        win.close()

        assert config_path.exists()

    def test_bad_splitter_sizes_falls_back_to_default(self, window):
        """配置写坏也不能崩；Qt 会按窗口实际宽度裁剪尺寸，所以只看有没有两段。"""
        win, params, _ = window
        params.fixed.splitter_sizes = "not-a-list"

        win._load_settings()  # 不能崩

        assert len(win.splitter.sizes()) == 2


class TestRendering:
    def test_count_snapshot_renders_labels(self, window):
        win, _, _ = window
        snap = make_count_snapshot(
            state=CounterState.NORMAL,
            total_pieces=7,
            avg_weight=10.25,
            tolerance_high=12.3,
            tolerance_low=8.2,
        )

        win._on_count_snapshot_changed(snap)

        assert win.lblTotalPieces.text() == "7"
        assert win.lblAvgWeight.text() == "10.25"
        assert win.lblTolHigh.text() == "12.30"
        assert win.lblTolLow.text() == "8.20"

    def test_count_snapshot_feeds_piece_table(self, window):
        win, _, _ = window
        snap = make_count_snapshot(piece_weights=[10.0, 20.0])

        win._on_count_snapshot_changed(snap)

        assert win.wgtPieceTable.rowCount() == 2
        assert win.wgtPieceTable.item(0, 0).text() == "20.00"  # 最新在顶

    def test_bar_snapshot_updates_status_labels(self, window):
        win, _, _ = window
        from app.presentation.bar_state import BarState

        bar = BarState().on_timeout()
        win._on_bar_snapshot_changed(bar)

        assert "等待" in win.lblParse.text()
        assert "等待" in win.lblComm.text()
