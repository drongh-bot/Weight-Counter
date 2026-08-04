from unittest.mock import MagicMock

import pytest
from PySide6.QtTest import QSignalSpy

from app.models.counter_state import CounterState
from app.presentation.status_bar import (
    MSG_ABNORMAL,
    MSG_FORCE_DONE,
    MSG_FORCE_FAIL,
    MSG_TARGET,
    MSG_WAIT_STABLE,
    ForceOutcome,
)
class TestControllerPipeline:
    def test_raw_data_pipeline(self, make_controller):
        controller, ui = make_controller()
        controller._is_running = True
        spy = QSignalSpy(ui.actual_weight_changed)

        initial_count = spy.count()
        controller._on_raw_data("10.0 kg")

        assert spy.count() > initial_count

    def test_raw_data_ignored_when_not_running(self, make_controller):
        controller, ui = make_controller()
        spy = QSignalSpy(ui.actual_weight_changed)
        initial_count = spy.count()
        controller._on_raw_data("10.0 kg")
        assert spy.count() == initial_count

    def test_unstable_does_not_overwrite_status_message(self, make_controller):
        controller, ui = make_controller()
        controller._is_running = True
        ui.update_bar(controller._bar.on_csv_error("测试保留信息"))

        controller._on_raw_data("10.0 kg")  # 未稳定，不应改写 message
        assert ui._last_bar is not None
        assert ui._last_bar.message.text == "测试保留信息"

    def test_on_timeout_updates_status(self, make_controller):
        controller, ui = make_controller()
        spy = QSignalSpy(ui.bar_snapshot_changed)

        controller._on_timeout()

        assert spy.count() >= 1
        d = spy.at(spy.count() - 1)[0]
        assert d.parse.text == "解析等待"
        assert d.comm.text == "通讯等待"

    def test_on_timeout_preserves_status_message(self, make_controller):
        controller, ui = make_controller()
        ui.update_bar(
            controller._bar.on_stable_frame(
                state=CounterState.ABNORMAL,
                force=ForceOutcome.NONE,
                target_reached=False,
                piece_added=False,
            )
        )

        controller._on_timeout()

        assert ui._last_bar is not None
        assert ui._last_bar.message.text == MSG_ABNORMAL
        assert ui._last_bar.comm.text == "通讯等待"

    def test_on_error_updates_status(self, make_controller):
        controller, ui = make_controller()
        spy = QSignalSpy(ui.bar_snapshot_changed)

        controller._on_serial_error("测试错误")

        assert spy.count() >= 1
        d = spy.at(spy.count() - 1)[0]
        assert d.message.text == "测试错误"

    def test_force_calibrate_pending(self, make_controller):
        controller, ui = make_controller()
        controller._is_running = True
        spy = QSignalSpy(ui.bar_snapshot_changed)
        controller.force_calibrate(5)
        assert controller._pending_force_pieces == 5
        d = spy.at(spy.count() - 1)[0]
        assert d.message.text == MSG_WAIT_STABLE

    def test_force_calibrate_ignored_when_pieces_zero(self, make_controller):
        controller, ui = make_controller()
        controller._is_running = True
        controller.force_calibrate(0)
        assert controller._pending_force_pieces is None

    def test_force_calibrate_executes_on_next_stable(self, make_controller):
        controller, ui = make_controller()
        controller._is_running = True

        for _ in range(12):
            controller._on_raw_data("10.0 kg")

        controller.force_calibrate(3)
        assert controller._pending_force_pieces == 3

        for _ in range(12):
            controller._on_raw_data("30.0 kg")

        result = controller.counter_service.current_result()
        assert result.total_pieces == 3
        assert controller._pending_force_pieces is None

    def test_force_calibrate_from_normal_without_abnormal(self, make_controller):
        """NORMAL 状态下也可强制校准，无需先进入异常"""
        controller, ui = make_controller()
        controller._is_running = True

        for _ in range(12):
            controller._on_raw_data("10.0 kg")
        assert controller.counter_service.current_result().state == CounterState.NORMAL

        # 先稳定在 30，再强制校准，避免 pending 在过渡帧用旧 stable 重量执行
        for _ in range(12):
            controller._on_raw_data("30.0 kg")
        controller.force_calibrate(3)
        for _ in range(12):
            controller._on_raw_data("30.0 kg")

        result = controller.counter_service.current_result()
        assert result.state == CounterState.NORMAL
        assert result.total_pieces == 3
        assert result.baseline_weight == pytest.approx(30.0)

    def test_abnormal_auto_recovers_when_weight_returns(self, make_controller):
        controller, ui = make_controller()
        controller._is_running = True

        for _ in range(12):
            controller._on_raw_data("10.0 kg")
        for _ in range(12):
            controller._on_raw_data("25.0 kg")
        assert controller.counter_service.current_result().state == CounterState.ABNORMAL

        for _ in range(12):
            controller._on_raw_data("10.0 kg")
        assert controller.counter_service.current_result().state == CounterState.NORMAL

    def test_abnormal_status_persists_until_recovered(self, make_controller):
        sound = MagicMock()
        controller, ui = make_controller(sound_service=sound)
        controller._is_running = True

        for _ in range(12):
            controller._on_raw_data("10.0 kg")
        for _ in range(12):
            controller._on_raw_data("25.0 kg")
            if controller.counter_service.current_result().state == CounterState.ABNORMAL:
                break

        assert controller.counter_service.current_result().state == CounterState.ABNORMAL
        sound.play_error.assert_called()
        assert ui._last_bar is not None
        assert ui._last_bar.message.text == MSG_ABNORMAL

        # still abnormal: message must stick across further stable frames
        for _ in range(5):
            controller._on_raw_data("25.0 kg")
        assert controller.counter_service.current_result().state == CounterState.ABNORMAL
        assert ui._last_bar.message.text == MSG_ABNORMAL

        for _ in range(12):
            controller._on_raw_data("10.0 kg")
        assert controller.counter_service.current_result().state == CounterState.NORMAL
        assert ui._last_bar.message.text == "无异常"

    def test_target_status_persists_until_next_add(self, make_controller):
        sound = MagicMock()
        controller, ui = make_controller(sound_service=sound, target_pieces=2)
        controller._is_running = True

        for _ in range(12):
            controller._on_raw_data("10.0 kg")
        for _ in range(12):
            controller._on_raw_data("20.0 kg")
            if controller.counter_service.current_result().total_pieces >= 2:
                break

        assert controller.counter_service.current_result().total_pieces == 2
        sound.play_alert.assert_called()
        assert ui._last_bar is not None
        assert ui._last_bar.message.text == MSG_TARGET

        # no new pieces: target message sticks
        for _ in range(5):
            controller._on_raw_data("20.0 kg")
        assert controller.counter_service.current_result().total_pieces == 2
        assert ui._last_bar.message.text == MSG_TARGET

        # next add clears target hold
        for _ in range(12):
            controller._on_raw_data("30.0 kg")
            if controller.counter_service.current_result().total_pieces >= 3:
                break
        assert controller.counter_service.current_result().total_pieces == 3
        assert ui._last_bar.message.text == "无异常"

    def test_pending_only_when_running(self, make_controller):
        controller, ui = make_controller()
        controller._is_running = False

        controller.force_calibrate(5)
        assert controller._pending_force_pieces is None

    def test_stop_resets_all(self, make_controller):
        controller, ui = make_controller()
        controller._is_running = True

        for _ in range(12):
            controller._on_raw_data("10.0 kg")
        assert controller.counter_service.current_result().total_pieces == 1

        controller.stop()
        assert controller._is_running is False
        assert controller.counter_service.current_result().total_pieces == 0
        assert controller._pending_force_pieces is None

    def test_start_resets_and_starts_serial(self, make_controller):
        controller, ui = make_controller()
        controller._is_running = True
        for _ in range(12):
            controller._on_raw_data("10.0 kg")

        original_open = controller.serial_service.open
        controller.serial_service.open = MagicMock()
        original_close = controller.serial_service.close
        controller.serial_service.close = MagicMock()

        try:
            controller.start("COM99", 9600)
            assert controller._is_running is True
            assert controller.counter_service.current_result().total_pieces == 0
            controller.serial_service.open.assert_called_once_with("COM99", 9600)
        finally:
            controller.serial_service.open = original_open
            controller.serial_service.close = original_close

    def test_ui_button_state_when_running(self, make_controller):
        controller, ui = make_controller()
        spy = QSignalSpy(ui.button_status_changed)

        controller._is_running = True
        controller._sync_button_status()

        d = spy.at(spy.count() - 1)[0]
        assert d.start_enabled is False
        assert d.stop_enabled is True
        assert d.force_enabled is True
        assert d.start_params_enabled is False

    def test_start_params_enabled_when_stopped(self, make_controller):
        controller, ui = make_controller()
        status = controller._button_status()
        assert status.start_params_enabled is True
        assert status.start_enabled is True

    def test_ui_button_state_when_abnormal(self, make_controller):
        controller, ui = make_controller()
        controller._is_running = True

        for _ in range(12):
            controller._on_raw_data("10.0 kg")
        for _ in range(12):
            controller._on_raw_data("25.0 kg")

        result = controller.counter_service.current_result()
        assert result.state == CounterState.ABNORMAL

        status = controller._button_status()
        assert status.force_enabled is True

    def test_force_pending_disables_force_button(self, make_controller):
        controller, ui = make_controller()
        controller._is_running = True
        for _ in range(12):
            controller._on_raw_data("10.0 kg")

        controller.force_calibrate(3)
        status = controller._button_status()
        assert status.force_enabled is False
        assert controller._pending_force_pieces == 3

        # duplicate request ignored while pending
        controller.force_calibrate(5)
        assert controller._pending_force_pieces == 3

    def test_force_calibrate_failed_shows_message(self, make_controller):
        controller, ui = make_controller()
        controller._is_running = True
        controller.force_calibrate(3)
        assert controller._pending_force_pieces == 3

        force, _ = controller._resolve_stable_frame(0.01)
        assert force is ForceOutcome.FAIL
        assert controller._pending_force_pieces is None
        ui.update_bar(
            controller._bar.on_stable_frame(
                state=controller.counter_service.current_result().state,
                force=ForceOutcome.FAIL,
                target_reached=False,
                piece_added=False,
            )
        )
        assert ui._last_bar is not None
        assert ui._last_bar.message.text == MSG_FORCE_FAIL
        assert controller._button_status().force_enabled is True

    def test_raw_mismatches_stable(self, make_controller):
        controller, ui = make_controller()
        controller.params.stability_threshold = 0.02
        controller.weight_input_service.apply_start_params()
        assert controller._raw_mismatches_stable(30.0, 10.0) is True
        assert controller._raw_mismatches_stable(10.01, 10.0) is False
        assert controller._raw_mismatches_stable(10.0, 10.0) is False

    def test_force_calibrate_waits_when_raw_stable_mismatch(self, make_controller):
        """NORMAL 下强制校准：raw/stable 不一致时保持等待，不立刻执行"""
        controller, ui = make_controller()
        controller._is_running = True
        for _ in range(12):
            controller._on_raw_data("10.0 kg")
        assert controller.counter_service.current_result().total_pieces == 1

        controller.force_calibrate(3)
        assert ui._last_bar is not None
        assert ui._last_bar.message.text == MSG_WAIT_STABLE
        # 重量跳到 30，但 stable 仍锁在 10 → 应 defer，件数不变
        controller._on_raw_data("30.0 kg")
        assert controller._pending_force_pieces == 3
        assert controller.counter_service.current_result().total_pieces == 1
        assert ui._last_bar.message.text == MSG_WAIT_STABLE

    def test_force_calibrate_target_edge(self, make_controller):
        sound = MagicMock()
        controller, ui = make_controller(sound_service=sound, target_pieces=3)
        controller._is_running = True
        for _ in range(12):
            controller._on_raw_data("10.0 kg")
        assert controller.counter_service.current_result().total_pieces == 1
        controller.force_calibrate(3)

        saw_force_done = False
        for _ in range(12):
            controller._on_raw_data("30.0 kg")
            if ui._last_bar and ui._last_bar.message.text == MSG_FORCE_DONE:
                saw_force_done = True
        assert controller.counter_service.current_result().total_pieces == 3
        sound.play_alert.assert_called()
        assert saw_force_done
        assert controller._bar._hold_target is True
        # subsequent stable frames (no new add): sticky target
        for _ in range(3):
            controller._on_raw_data("30.0 kg")
        assert ui._last_bar is not None
        assert ui._last_bar.message.text == MSG_TARGET
        assert controller._button_status().force_enabled is True

    def test_parse_fail_clears_actual_weight(self, make_controller):
        controller, ui = make_controller()
        spy = QSignalSpy(ui.actual_weight_changed)
        controller._is_running = True
        for _ in range(12):
            controller._on_raw_data("10.0 kg")
        controller._on_raw_data("not-a-weight")
        assert spy.at(spy.count() - 1)[0] == "-----"

    def test_decimal_places_applies_on_start_only(self, make_controller):
        controller, ui = make_controller()
        controller._is_running = True
        controller.counter_service.process(10.0)
        controller.params.decimal_places = 4
        # mid-run: Params changed but algorithm keeps old decimal places
        assert controller.counter_service.current_result().decimal_places == 2

        controller.serial_service.open = MagicMock()
        controller.serial_service.close = MagicMock()
        controller.start("COM99", 9600)
        assert controller.counter_service.current_result().decimal_places == 4
