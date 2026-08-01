from PySide6.QtTest import QSignalSpy

from app.models.count_result import CountResult
from app.models.counter_state import CounterState
from app.services.ui.view_models import ButtonStatus
from app.services.ui.styles import Styles
from app.services.ui.ui_service import UIService


class TestUIService:
    @staticmethod
    def _last(spy):
        return spy.at(spy.count() - 1)[0]

    def test_update_count_emits(self, qapp):
        svc = UIService()
        spy = QSignalSpy(svc.count_changed)

        biz = CountResult(
            added=True, abnormal_high=False, abnormal_low=False,
            state=CounterState.NORMAL, delta=10.0, avg_weight=10.0,
            tol_high=11.0, tol_low=9.0, total_pieces=1,
            last_stable_weight=10.0, last_base_weight=0.0, weights=[10.0],
        )
        svc.update_count(biz)

        assert spy.count() == 1
        d = self._last(spy)
        assert d.state.text == "正常"

    def test_count_duplicate_not_emitted(self, qapp):
        svc = UIService()
        spy = QSignalSpy(svc.count_changed)

        biz = CountResult(
            added=False, abnormal_high=False, abnormal_low=False,
            state=CounterState.ZERO, delta=0.0, avg_weight=0.0,
            tol_high=0.0, tol_low=0.0, total_pieces=0,
            last_stable_weight=0.0, last_base_weight=0.0, weights=[],
        )
        svc.update_count(biz)
        assert spy.count() == 1

        svc.update_count(biz)
        assert spy.count() == 1

    def test_count_different_data_emits_again(self, qapp):
        svc = UIService()
        spy = QSignalSpy(svc.count_changed)

        biz = CountResult(
            added=False, abnormal_high=False, abnormal_low=False,
            state=CounterState.ZERO, delta=0.0, avg_weight=0.0,
            tol_high=0.0, tol_low=0.0, total_pieces=0,
            last_stable_weight=0.0, last_base_weight=0.0, weights=[],
        )
        svc.update_count(biz)
        assert spy.count() == 1

        biz2 = CountResult(
            added=True, abnormal_high=False, abnormal_low=False,
            state=CounterState.NORMAL, delta=10.0, avg_weight=10.0,
            tol_high=11.0, tol_low=9.0, total_pieces=1,
            last_stable_weight=10.0, last_base_weight=0.0, weights=[10.0],
        )
        svc.update_count(biz2)
        assert spy.count() == 2

    def test_refresh_re_emits_last(self, qapp):
        svc = UIService()
        count_spy = QSignalSpy(svc.count_changed)
        bar_spy = QSignalSpy(svc.bar_status_changed)
        btn_spy = QSignalSpy(svc.button_status_changed)

        result = CountResult(
            added=False, abnormal_high=False, abnormal_low=False,
            state=CounterState.ZERO, delta=0.0, avg_weight=0.0,
            tol_high=0.0, tol_low=0.0, total_pieces=0,
            last_stable_weight=0.0, last_base_weight=0.0, weights=[],
        )
        svc.update_count(result)
        svc.update_bar_status()
        svc.update_button_status(ButtonStatus())
        assert count_spy.count() == 1
        assert bar_spy.count() == 1
        assert btn_spy.count() == 1

        svc.refresh()
        assert count_spy.count() == 2
        assert bar_spy.count() == 2
        assert btn_spy.count() == 2

    def test_bar_status_fields_propagated(self, qapp):
        svc = UIService()
        spy = QSignalSpy(svc.bar_status_changed)

        svc.update_bar_status(
            parse_ok=True, comm_ok=False, status_message="测试异常"
        )

        d = self._last(spy)
        assert d.parse.text == "解析等待"
        assert d.parse.style == Styles.GRAY
        assert d.comm.text == "通讯等待"
        assert d.comm.style == Styles.GRAY
        assert d.message.text == "测试异常"
        assert d.message.style == Styles.RED

    def test_actual_weight_none_shows_dashes(self, qapp):
        svc = UIService()
        spy = QSignalSpy(svc.actual_weight_changed)

        svc.update_actual_weight(None, decimal_places=2)

        d = self._last(spy)
        assert d == "-----"

    def test_actual_weight_value_formatted(self, qapp):
        svc = UIService()
        spy = QSignalSpy(svc.actual_weight_changed)

        svc.update_actual_weight(10.0, decimal_places=2)

        d = self._last(spy)
        assert d == "10.00"

    def test_button_status_emits(self, qapp):
        svc = UIService()
        spy = QSignalSpy(svc.button_status_changed)

        svc.update_button_status(ButtonStatus(start=False, stop=True))
        assert spy.count() == 1
        d = self._last(spy)
        assert d.start is False
        assert d.stop is True

    def test_button_status_duplicate_not_emitted(self, qapp):
        svc = UIService()
        spy = QSignalSpy(svc.button_status_changed)

        state = ButtonStatus(start=False, stop=True)
        svc.update_button_status(state)
        assert spy.count() == 1
        svc.update_button_status(state)
        assert spy.count() == 1
