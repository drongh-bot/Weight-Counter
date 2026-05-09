from unittest.mock import MagicMock

from PySide6.QtTest import QSignalSpy

from app.controllers.main_controller import MainController, PendingAction
from app.models.biz_result import BizState
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

    @staticmethod
    def _last_ui(spy):
        return spy.at(spy.count() - 1)[0]

    def test_raw_data_pipeline(self, qapp):
        controller, ui = self._make_controller(qapp)
        spy = QSignalSpy(ui.ui_changed)

        initial_count = spy.count()
        controller._on_raw_data("10.0 kg")

        # 解析 + 稳定检测后应有 UI 更新
        assert spy.count() > initial_count

    def test_on_timeout_updates_status(self, qapp):
        controller, ui = self._make_controller(qapp)
        spy = QSignalSpy(ui.ui_changed)

        controller._on_timeout()

        assert spy.count() >= 1
        d = self._last_ui(spy)
        assert d.status.parse.text == "解析等待"
        assert d.status.comm.text == "通讯等待"

    def test_on_error_updates_status(self, qapp):
        controller, ui = self._make_controller(qapp)
        spy = QSignalSpy(ui.ui_changed)

        controller._on_serial_error("测试错误")

        assert spy.count() >= 1
        d = self._last_ui(spy)
        assert d.status.exception.text == "测试错误"

    def test_force_accept_pending_action(self, qapp):
        controller, ui = self._make_controller(qapp)
        controller.running = True
        controller.force_accept(5)
        assert controller._pending_action == PendingAction.FORCE_ACCEPT

    def test_clear_abnormal_pending_action(self, qapp):
        controller, ui = self._make_controller(qapp)
        controller.running = True
        controller.clear_abnormal()
        assert controller._pending_action == PendingAction.CLEAR_ABNORMAL

    def test_force_accept_executes_on_next_stable(self, qapp):
        controller, ui = self._make_controller(qapp)
        controller.running = True

        # 建立基准（喂入多帧以通过稳定检测）
        for _ in range(12):
            controller._on_raw_data("10.0 kg")

        # 排队强制校准
        controller.force_accept(3)
        assert controller._pending_action == PendingAction.FORCE_ACCEPT

        # 下一帧稳定重量 → 应执行强制校准
        for _ in range(12):
            controller._on_raw_data("30.0 kg")

        # 强制校准后计数器应重置为 3 件
        result = controller.counter_service.current_result()
        assert result.total_pieces == 3
        assert controller._pending_action == PendingAction.NONE

    def test_clear_abnormal_executes(self, qapp):
        controller, ui = self._make_controller(qapp)
        controller.running = True

        # 建立基准
        for _ in range(12):
            controller._on_raw_data("10.0 kg")
        # 制造异常（delta=15 无法匹配，需多帧稳定）
        for _ in range(12):
            controller._on_raw_data("25.0 kg")
        result = controller.counter_service.current_result()
        assert result.state == BizState.ABNORMAL

        # 排队清除异常
        controller.clear_abnormal()
        # 下一帧执行
        controller._on_raw_data("10.0 kg")

        result = controller.counter_service.current_result()
        assert result.state != BizState.ABNORMAL
        assert controller._pending_action == PendingAction.NONE

    def test_pending_action_only_when_running(self, qapp):
        controller, ui = self._make_controller(qapp)
        controller.running = False

        controller.force_accept(5)
        assert controller._pending_action == PendingAction.NONE

        controller.clear_abnormal()
        assert controller._pending_action == PendingAction.NONE

    def test_stop_resets_all(self, qapp):
        controller, ui = self._make_controller(qapp)
        controller.running = True

        for _ in range(12):
            controller._on_raw_data("10.0 kg")
        assert controller.counter_service.current_result().total_pieces == 1

        controller.stop()
        assert controller.running is False
        assert controller.counter_service.current_result().total_pieces == 0
        assert controller._pending_action == PendingAction.NONE

    def test_start_resets_and_starts_serial(self, qapp):
        controller, ui = self._make_controller(qapp)
        controller.running = True
        for _ in range(12):
            controller._on_raw_data("10.0 kg")

        # mock serial.open 避免真实串口
        original_open = controller.serial_service.open
        controller.serial_service.open = MagicMock()
        original_close = controller.serial_service.close
        controller.serial_service.close = MagicMock()

        try:
            controller.start("COM99", 9600)
            assert controller.running is True
            assert controller.counter_service.current_result().total_pieces == 0
            controller.serial_service.open.assert_called_once_with("COM99", 9600)
        finally:
            controller.serial_service.open = original_open
            controller.serial_service.close = original_close

    def test_ui_button_state_when_running(self, qapp):
        controller, ui = self._make_controller(qapp)
        spy = QSignalSpy(ui.ui_changed)

        controller.running = True
        controller._update_ui(controller.counter_service.current_result(), 10.0)

        d = self._last_ui(spy)
        assert d.button_state.start is False
        assert d.button_state.stop is True

    def test_ui_button_state_when_abnormal(self, qapp):
        controller, ui = self._make_controller(qapp)
        controller.running = True

        # 先建立基准
        for _ in range(12):
            controller._on_raw_data("10.0 kg")
        # 再制造异常
        for _ in range(12):
            controller._on_raw_data("25.0 kg")

        result = controller.counter_service.current_result()
        assert result.state == BizState.ABNORMAL
