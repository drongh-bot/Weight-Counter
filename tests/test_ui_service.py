from PySide6.QtTest import QSignalSpy

from app.models.biz_result import BizResult
from app.models.counter_state import CounterState
from app.services.ui.models import ButtonStatus
from app.services.ui.styles import Styles
from app.services.ui.ui_service import UIService


class TestUIService:
    @staticmethod
    def _last(spy):
        return spy.at(spy.count() - 1)[0]

    def test_update_biz_emits(self, qapp):
        svc = UIService()
        spy = QSignalSpy(svc.biz_changed)

        biz = BizResult(
            added=True, abnormal_high=False, abnormal_low=False,
            state=CounterState.NORMAL, delta=10.0, avg_weight=10.0,
            tol_high=11.0, tol_low=9.0, total_pieces=1,
            last_stable_weight=10.0, last_base_weight=0.0, weights=[10.0],
        )
        svc.update_biz(biz)

        assert spy.count() == 1
        d = self._last(spy)
        assert d.state.text == "正常"

    def test_biz_duplicate_not_emitted(self, qapp):
        svc = UIService()
        spy = QSignalSpy(svc.biz_changed)

        biz = BizResult(
            added=False, abnormal_high=False, abnormal_low=False,
            state=CounterState.ZERO, delta=0.0, avg_weight=0.0,
            tol_high=0.0, tol_low=0.0, total_pieces=0,
            last_stable_weight=0.0, last_base_weight=0.0, weights=[],
        )
        svc.update_biz(biz)
        assert spy.count() == 1

        svc.update_biz(biz)
        assert spy.count() == 1

    def test_biz_different_data_emits_again(self, qapp):
        svc = UIService()
        spy = QSignalSpy(svc.biz_changed)

        biz = BizResult(
            added=False, abnormal_high=False, abnormal_low=False,
            state=CounterState.ZERO, delta=0.0, avg_weight=0.0,
            tol_high=0.0, tol_low=0.0, total_pieces=0,
            last_stable_weight=0.0, last_base_weight=0.0, weights=[],
        )
        svc.update_biz(biz)
        assert spy.count() == 1

        biz2 = BizResult(
            added=True, abnormal_high=False, abnormal_low=False,
            state=CounterState.NORMAL, delta=10.0, avg_weight=10.0,
            tol_high=11.0, tol_low=9.0, total_pieces=1,
            last_stable_weight=10.0, last_base_weight=0.0, weights=[10.0],
        )
        svc.update_biz(biz2)
        assert spy.count() == 2

    def test_refresh_re_emits_last(self, qapp):
        svc = UIService()
        biz_spy = QSignalSpy(svc.biz_changed)
        bar_spy = QSignalSpy(svc.bar_status_changed)
        btn_spy = QSignalSpy(svc.button_status_changed)

        biz = BizResult(
            added=False, abnormal_high=False, abnormal_low=False,
            state=CounterState.ZERO, delta=0.0, avg_weight=0.0,
            tol_high=0.0, tol_low=0.0, total_pieces=0,
            last_stable_weight=0.0, last_base_weight=0.0, weights=[],
        )
        svc.update_biz(biz)
        svc.update_bar_status()
        svc.update_button_status(ButtonStatus())
        assert biz_spy.count() == 1
        assert bar_spy.count() == 1
        assert btn_spy.count() == 1

        svc.refresh()
        assert biz_spy.count() == 2
        assert bar_spy.count() == 2
        assert btn_spy.count() == 2

    def test_bar_status_fields_propagated(self, qapp):
        svc = UIService()
        spy = QSignalSpy(svc.bar_status_changed)

        svc.update_bar_status(
            parse_ok=True, comm_ok=False, exception_text="测试异常"
        )

        d = self._last(spy)
        assert d.parse.text == "解析等待"
        assert d.parse.style == Styles.GRAY
        assert d.comm.text == "通讯等待"
        assert d.comm.style == Styles.GRAY
        assert d.exception.text == "测试异常"
        assert d.exception.style == Styles.RED

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
