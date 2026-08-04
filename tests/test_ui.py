from PySide6.QtTest import QSignalSpy

from app.models.counter_state import CounterState
from app.presentation.status_bar import StatusBar
from app.presentation.styles import Styles
from app.presentation.ui import UiBridge
from app.presentation.view_models import ButtonStatus
from tests.conftest import make_count_result


class TestUi:
    @staticmethod
    def _last(spy):
        return spy.at(spy.count() - 1)[0]

    def test_update_count_emits(self, qapp):
        ui = UiBridge()
        spy = QSignalSpy(ui.count_changed)

        ui.update_count(
            make_count_result(
                added=True,
                state=CounterState.NORMAL,
                delta=10.0,
                avg_weight=10.0,
                tolerance_high=11.0,
                tolerance_low=9.0,
                total_pieces=1,
                last_stable_weight=10.0,
                piece_weights=[10.0],
            )
        )

        assert spy.count() == 1
        d = self._last(spy)
        assert d.state.text == "正常"

    def test_count_duplicate_not_emitted(self, qapp):
        ui = UiBridge()
        spy = QSignalSpy(ui.count_changed)

        result = make_count_result()
        ui.update_count(result)
        assert spy.count() == 1

        ui.update_count(result)
        assert spy.count() == 1

    def test_count_different_data_emits_again(self, qapp):
        ui = UiBridge()
        spy = QSignalSpy(ui.count_changed)

        ui.update_count(make_count_result())
        assert spy.count() == 1

        ui.update_count(
            make_count_result(
                added=True,
                state=CounterState.NORMAL,
                delta=10.0,
                avg_weight=10.0,
                tolerance_high=11.0,
                tolerance_low=9.0,
                total_pieces=1,
                last_stable_weight=10.0,
                piece_weights=[10.0],
            )
        )
        assert spy.count() == 2

    def test_refresh_re_emits_last(self, qapp):
        ui = UiBridge()
        count_spy = QSignalSpy(ui.count_changed)
        bar_spy = QSignalSpy(ui.bar_snapshot_changed)
        btn_spy = QSignalSpy(ui.button_status_changed)

        ui.update_count(make_count_result())
        ui.update_bar(StatusBar().reset())
        ui.update_button_status(ButtonStatus())
        assert count_spy.count() == 1
        assert bar_spy.count() == 1
        assert btn_spy.count() == 1

        ui.refresh()
        assert count_spy.count() == 2
        assert bar_spy.count() == 2
        assert btn_spy.count() == 2

    def test_update_bar_fields(self, qapp):
        ui = UiBridge()
        spy = QSignalSpy(ui.bar_snapshot_changed)

        ui.update_bar(StatusBar().on_serial_error("测试异常"))

        d = self._last(spy)
        assert d.parse.text == "解析等待"
        assert d.parse.style == Styles.GRAY
        assert d.comm.text == "通讯等待"
        assert d.comm.style == Styles.GRAY
        assert d.message.text == "测试异常"
        assert d.message.style == Styles.RED

    def test_update_bar_duplicate_not_emitted(self, qapp):
        ui = UiBridge()
        spy = QSignalSpy(ui.bar_snapshot_changed)
        status = StatusBar().on_force_waiting()
        ui.update_bar(status)
        ui.update_bar(status)
        assert spy.count() == 1

    def test_actual_weight_none_shows_dashes(self, qapp):
        ui = UiBridge()
        spy = QSignalSpy(ui.actual_weight_changed)

        ui.update_actual_weight(None, decimal_places=2)

        d = self._last(spy)
        assert d == "-----"

    def test_actual_weight_value_formatted(self, qapp):
        ui = UiBridge()
        spy = QSignalSpy(ui.actual_weight_changed)

        ui.update_actual_weight(10.0, decimal_places=2)

        d = self._last(spy)
        assert d == "10.00"

    def test_button_status_emits(self, qapp):
        ui = UiBridge()
        spy = QSignalSpy(ui.button_status_changed)

        ui.update_button_status(ButtonStatus(start_enabled=False, stop_enabled=True))
        assert spy.count() == 1
        d = self._last(spy)
        assert d.start_enabled is False
        assert d.stop_enabled is True

    def test_button_status_duplicate_not_emitted(self, qapp):
        ui = UiBridge()
        spy = QSignalSpy(ui.button_status_changed)

        state = ButtonStatus(start_enabled=False, stop_enabled=True)
        ui.update_button_status(state)
        assert spy.count() == 1
        ui.update_button_status(state)
        assert spy.count() == 1
