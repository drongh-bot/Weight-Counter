from unittest.mock import MagicMock

from PySide6.QtTest import QSignalSpy

from app.controllers.main_controller import MainController, PendingAction
from app.models.counter_state import CounterState
from app.models.params import Params
from app.services.checker_service import CheckerService
from app.services.counter_service import CounterService
from app.services.csv_log_service import CsvLogService
from app.services.serial_service import SerialService
from app.services.sound_service import SoundService
from app.services.ui.ui_service import UIService


class TestControllerPipeline:
    @staticmethod
    def _make_controller(qapp):
        params = Params()
        params.target_pieces = 10
        params.max_batch_pieces = 4

        ui = UIService()
        serial = SerialService(2000)
        counter = CounterService(params)
        checker = CheckerService(params)
        sound = SoundService()
        csv_log = CsvLogService()

        controller = MainController(
            ui_service=ui,
            serial_service=serial,
            counter_service=counter,
            checker_service=checker,
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
        assert d.exception.text == "测试错误"

    def test_force_accept_pending_action(self, qapp):
        controller, ui = self._make_controller(qapp)
        controller._is_active = True
        controller.force_accept(5)
        assert controller._pending_action == PendingAction.FORCE_ACCEPT

    def test_clear_abnormal_pending_action(self, qapp):
        controller, ui = self._make_controller(qapp)
        controller._is_active = True
        controller.clear_abnormal()
        assert controller._pending_action == PendingAction.CLEAR_ABNORMAL

    def test_force_accept_executes_on_next_stable(self, qapp):
        controller, ui = self._make_controller(qapp)
        controller._is_active = True

        for _ in range(12):
            controller._on_raw_data("10.0 kg")

        controller.force_accept(3)
        assert controller._pending_action == PendingAction.FORCE_ACCEPT

        for _ in range(12):
            controller._on_raw_data("30.0 kg")

        result = controller.counter_service.current_result()
        assert result.total_pieces == 3
        assert controller._pending_action == PendingAction.NONE

    def test_clear_abnormal_executes(self, qapp):
        controller, ui = self._make_controller(qapp)
        controller._is_active = True

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
        assert controller._pending_action == PendingAction.NONE

    def test_pending_action_only_when_running(self, qapp):
        controller, ui = self._make_controller(qapp)
        controller._is_active = False

        controller.force_accept(5)
        assert controller._pending_action == PendingAction.NONE

        controller.clear_abnormal()
        assert controller._pending_action == PendingAction.NONE

    def test_stop_resets_all(self, qapp):
        controller, ui = self._make_controller(qapp)
        controller._is_active = True

        for _ in range(12):
            controller._on_raw_data("10.0 kg")
        assert controller.counter_service.current_result().total_pieces == 1

        controller.stop()
        assert controller._is_active is False
        assert controller.counter_service.current_result().total_pieces == 0
        assert controller._pending_action == PendingAction.NONE

    def test_start_resets_and_starts_serial(self, qapp):
        controller, ui = self._make_controller(qapp)
        controller._is_active = True
        for _ in range(12):
            controller._on_raw_data("10.0 kg")

        original_open = controller.serial_service.open
        controller.serial_service.open = MagicMock()
        original_close = controller.serial_service.close
        controller.serial_service.close = MagicMock()

        try:
            controller.start("COM99", 9600)
            assert controller._is_active is True
            assert controller.counter_service.current_result().total_pieces == 0
            controller.serial_service.open.assert_called_once_with("COM99", 9600)
        finally:
            controller.serial_service.open = original_open
            controller.serial_service.close = original_close

    def test_ui_button_state_when_running(self, qapp):
        controller, ui = self._make_controller(qapp)
        spy = QSignalSpy(ui.button_status_changed)

        controller._is_active = True
        result = controller.counter_service.current_result()
        controller.ui_service.update_button_status(controller._button_status(result.state, controller._is_active))

        d = spy.at(spy.count() - 1)[0]
        assert d.start is False
        assert d.stop is True

    def test_ui_button_state_when_abnormal(self, qapp):
        controller, ui = self._make_controller(qapp)
        controller._is_active = True

        for _ in range(12):
            controller._on_raw_data("10.0 kg")
        for _ in range(12):
            controller._on_raw_data("25.0 kg")

        result = controller.counter_service.current_result()
        assert result.state == CounterState.ABNORMAL
