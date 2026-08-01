from unittest.mock import MagicMock

import pytest
from PySide6.QtTest import QSignalSpy

from app.controllers.main_controller import MainController
from app.models.counter_state import CounterState
from app.models.params import Params
from app.services.counter_service import CounterService
from app.services.csv_log_service import CsvLogService
from app.services.serial_service import SerialService
from app.services.sound_service import SoundService
from app.services.ui.ui_service import UIService
from app.services.weight_input_service import WeightInputService


class TestControllerPipeline:
    @staticmethod
    def _make_controller(qapp):
        params = Params()
        params.target_pieces = 10
        params.max_batch_pieces = 4

        ui = UIService()
        serial = SerialService(2000)
        counter = CounterService(params)
        weight_input = WeightInputService(params)
        sound = SoundService()
        csv_log = CsvLogService()

        controller = MainController(
            ui_service=ui,
            serial_service=serial,
            counter_service=counter,
            weight_input_service=weight_input,
            sound_service=sound,
            csv_log_service=csv_log,
            params=params,
        )
        return controller, ui

    def test_raw_data_pipeline(self, qapp):
        controller, ui = self._make_controller(qapp)
        spy = QSignalSpy(ui.actual_weight_changed)

        initial_count = spy.count()
        controller._on_raw_data("10.0 kg")

        assert spy.count() > initial_count

    def test_unstable_shows_waiting_stable_message(self, qapp):
        controller, ui = self._make_controller(qapp)
        controller._is_running = True

        controller._on_raw_data("10.0 kg")
        assert ui._last_bar is not None
        assert ui._last_bar.message.text == "等待稳定重量…"

        for _ in range(12):
            controller._on_raw_data("10.0 kg")
        assert ui._last_bar.message.text == "无异常"

    def test_on_timeout_updates_status(self, qapp):
        controller, ui = self._make_controller(qapp)
        spy = QSignalSpy(ui.bar_status_changed)

        controller._on_timeout()

        assert spy.count() >= 1
        d = spy.at(spy.count() - 1)[0]
        assert d.parse.text == "解析等待"
        assert d.comm.text == "通讯等待"

    def test_on_error_updates_status(self, qapp):
        controller, ui = self._make_controller(qapp)
        spy = QSignalSpy(ui.bar_status_changed)

        controller._on_serial_error("测试错误")

        assert spy.count() >= 1
        d = spy.at(spy.count() - 1)[0]
        assert d.message.text == "测试错误"

    def test_force_calibrate_pending(self, qapp):
        controller, ui = self._make_controller(qapp)
        controller._is_running = True
        spy = QSignalSpy(ui.bar_status_changed)
        controller.force_calibrate(5)
        assert controller._pending_force_pieces == 5
        assert controller._pending_clear_abnormal is False
        d = spy.at(spy.count() - 1)[0]
        assert d.message.text == "等待稳定重量…"

    def test_force_calibrate_ignored_when_pieces_zero(self, qapp):
        controller, ui = self._make_controller(qapp)
        controller._is_running = True
        controller.force_calibrate(0)
        assert controller._pending_force_pieces is None

    def test_clear_abnormal_pending(self, qapp):
        controller, ui = self._make_controller(qapp)
        controller._is_running = True
        controller.clear_abnormal()
        assert controller._pending_clear_abnormal is True
        assert controller._pending_force_pieces is None

    def test_force_calibrate_executes_on_next_stable(self, qapp):
        controller, ui = self._make_controller(qapp)
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

    def test_force_calibrate_from_normal_without_abnormal(self, qapp):
        """NORMAL 状态下也可强制校准，无需先进入异常"""
        controller, ui = self._make_controller(qapp)
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

    def test_clear_abnormal_executes(self, qapp):
        controller, ui = self._make_controller(qapp)
        controller._is_running = True

        for _ in range(12):
            controller._on_raw_data("10.0 kg")
        for _ in range(12):
            controller._on_raw_data("25.0 kg")
        result = controller.counter_service.current_result()
        assert result.state == CounterState.ABNORMAL

        controller.clear_abnormal()
        controller._on_raw_data("10.0 kg")

        result = controller.counter_service.current_result()
        assert result.state != CounterState.ABNORMAL
        assert controller._pending_clear_abnormal is False

    def test_pending_only_when_running(self, qapp):
        controller, ui = self._make_controller(qapp)
        controller._is_running = False

        controller.force_calibrate(5)
        assert controller._pending_force_pieces is None

        controller.clear_abnormal()
        assert controller._pending_clear_abnormal is False

    def test_stop_resets_all(self, qapp):
        controller, ui = self._make_controller(qapp)
        controller._is_running = True

        for _ in range(12):
            controller._on_raw_data("10.0 kg")
        assert controller.counter_service.current_result().total_pieces == 1

        controller.stop()
        assert controller._is_running is False
        assert controller.counter_service.current_result().total_pieces == 0
        assert controller._pending_force_pieces is None
        assert controller._pending_clear_abnormal is False

    def test_start_resets_and_starts_serial(self, qapp):
        controller, ui = self._make_controller(qapp)
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

    def test_ui_button_state_when_running(self, qapp):
        controller, ui = self._make_controller(qapp)
        spy = QSignalSpy(ui.button_status_changed)

        controller._is_running = True
        controller._sync_button_status()

        d = spy.at(spy.count() - 1)[0]
        assert d.start_enabled is False
        assert d.stop_enabled is True
        assert d.force_enabled is True
        assert d.clear_enabled is False

    def test_ui_button_state_when_abnormal(self, qapp):
        controller, ui = self._make_controller(qapp)
        controller._is_running = True

        for _ in range(12):
            controller._on_raw_data("10.0 kg")
        for _ in range(12):
            controller._on_raw_data("25.0 kg")

        result = controller.counter_service.current_result()
        assert result.state == CounterState.ABNORMAL

        status = controller._button_status()
        assert status.force_enabled is True
        assert status.clear_enabled is True

    def test_force_pending_disables_force_button(self, qapp):
        controller, ui = self._make_controller(qapp)
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

    def test_raw_mismatches_stable(self, qapp):
        controller, ui = self._make_controller(qapp)
        controller.params.stability_threshold = 0.02
        assert controller._raw_mismatches_stable(30.0, 10.0) is True
        assert controller._raw_mismatches_stable(10.01, 10.0) is False
        assert controller._raw_mismatches_stable(10.0, 10.0) is False

    def test_force_calibrate_waits_when_raw_stable_mismatch(self, qapp):
        """NORMAL 下强制校准：raw/stable 不一致时保持等待，不立刻执行"""
        controller, ui = self._make_controller(qapp)
        controller._is_running = True
        for _ in range(12):
            controller._on_raw_data("10.0 kg")
        assert controller.counter_service.current_result().total_pieces == 1

        controller.force_calibrate(3)
        assert ui._last_bar is not None
        assert ui._last_bar.message.text == "等待稳定重量…"
        # 重量跳到 30，但 stable 仍锁在 10 → 应 defer，件数不变
        controller._on_raw_data("30.0 kg")
        assert controller._pending_force_pieces == 3
        assert controller.counter_service.current_result().total_pieces == 1
        assert ui._last_bar.message.text == "等待稳定重量…"

    def test_force_calibrate_target_edge(self, qapp):
        sound = MagicMock()
        params = Params()
        params.target_pieces = 3
        ui = UIService()
        controller = MainController(
            ui,
            SerialService(2000),
            CounterService(params),
            WeightInputService(params),
            sound,
            CsvLogService(),
            params,
        )
        controller._is_running = True
        for _ in range(12):
            controller._on_raw_data("10.0 kg")
        assert controller.counter_service.current_result().total_pieces == 1
        controller.force_calibrate(3)
        for _ in range(12):
            controller._on_raw_data("30.0 kg")
        assert controller.counter_service.current_result().total_pieces == 3
        sound.play_alert.assert_called()
        assert ui._last_bar is not None
        assert ui._last_bar.message.text == "强制校准完成"
        assert controller._button_status().force_enabled is True

    def test_parse_fail_clears_actual_weight(self, qapp):
        controller, ui = self._make_controller(qapp)
        spy = QSignalSpy(ui.actual_weight_changed)
        controller._is_running = True
        for _ in range(12):
            controller._on_raw_data("10.0 kg")
        controller._on_raw_data("not-a-weight")
        assert spy.at(spy.count() - 1)[0] == "-----"

    def test_decimal_places_applies_on_start_only(self, qapp):
        controller, ui = self._make_controller(qapp)
        controller._is_running = True
        controller.counter_service.process(10.0)
        controller.params.decimal_places = 4
        # mid-run: Params changed but algorithm keeps old decimal places
        assert controller.counter_service.current_result().decimal_places == 2

        controller.serial_service.open = MagicMock()
        controller.serial_service.close = MagicMock()
        controller.start("COM99", 9600)
        assert controller.counter_service.current_result().decimal_places == 4
