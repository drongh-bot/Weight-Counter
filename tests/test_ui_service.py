from PySide6.QtTest import QSignalSpy

from app.models.biz_result import BizResult, BizState
from app.services.ui.models import ButtonState
from app.services.ui.styles import Styles
from app.services.ui.ui_service import UIService


class TestUIService:
    @staticmethod
    def _ui_data(spy, index=0):
        return spy.at(index)[0]

    def test_update_emits_ui_changed(self, qapp):
        svc = UIService()
        spy = QSignalSpy(svc.ui_changed)

        biz = BizResult(
            added=True,
            abnormal_high=False,
            abnormal_low=False,
            state=BizState.NORMAL,
            delta=10.0,
            avg_weight=10.0,
            tol_high=11.0,
            tol_low=9.0,
            total_pieces=1,
            last_stable_weight=10.0,
            last_base_weight=0.0,
            weights=[10.0],
        )
        btn = ButtonState(start=False, stop=True, clear=False, force=False)
        svc.update(biz, btn, actual_weight=10.0)

        assert spy.count() == 1
        d = self._ui_data(spy)
        assert d.actual_weight == "10.000"
        assert d.biz.state.text == "正常"
        assert d.button_state.start is False
        assert d.button_state.stop is True

    def test_duplicate_not_emitted(self, qapp):
        svc = UIService()
        spy = QSignalSpy(svc.ui_changed)

        biz = BizResult(
            added=False,
            abnormal_high=False,
            abnormal_low=False,
            state=BizState.ZERO,
            delta=0.0,
            avg_weight=0.0,
            tol_high=0.0,
            tol_low=0.0,
            total_pieces=0,
            last_stable_weight=0.0,
            last_base_weight=0.0,
            weights=[],
        )
        btn = ButtonState()
        svc.update(biz, btn, actual_weight=None)
        assert spy.count() == 1

        svc.update(biz, btn, actual_weight=None)
        assert spy.count() == 1  # 相同数据不重复发射

    def test_different_data_emits_again(self, qapp):
        svc = UIService()
        spy = QSignalSpy(svc.ui_changed)

        biz = BizResult(
            added=False,
            abnormal_high=False,
            abnormal_low=False,
            state=BizState.ZERO,
            delta=0.0,
            avg_weight=0.0,
            tol_high=0.0,
            tol_low=0.0,
            total_pieces=0,
            last_stable_weight=0.0,
            last_base_weight=0.0,
            weights=[],
        )
        btn = ButtonState()
        svc.update(biz, btn, actual_weight=None)
        assert spy.count() == 1

        biz2 = BizResult(
            added=True,
            abnormal_high=False,
            abnormal_low=False,
            state=BizState.NORMAL,
            delta=10.0,
            avg_weight=10.0,
            tol_high=11.0,
            tol_low=9.0,
            total_pieces=1,
            last_stable_weight=10.0,
            last_base_weight=0.0,
            weights=[10.0],
        )
        svc.update(biz2, btn, actual_weight=10.0)
        assert spy.count() == 2  # 不同数据重新发射

    def test_refresh_re_emits_last(self, qapp):
        svc = UIService()
        spy = QSignalSpy(svc.ui_changed)

        biz = BizResult(
            added=False,
            abnormal_high=False,
            abnormal_low=False,
            state=BizState.ZERO,
            delta=0.0,
            avg_weight=0.0,
            tol_high=0.0,
            tol_low=0.0,
            total_pieces=0,
            last_stable_weight=0.0,
            last_base_weight=0.0,
            weights=[],
        )
        svc.update(biz, ButtonState(), actual_weight=None)
        assert spy.count() == 1

        svc.refresh()
        assert spy.count() == 2
        # refresh 应发射相同数据
        assert self._ui_data(spy, 0) == self._ui_data(spy, 1)

    def test_status_fields_propagated(self, qapp):
        svc = UIService()
        spy = QSignalSpy(svc.ui_changed)

        biz = BizResult(
            added=False,
            abnormal_high=False,
            abnormal_low=False,
            state=BizState.ZERO,
            delta=0.0,
            avg_weight=0.0,
            tol_high=0.0,
            tol_low=0.0,
            total_pieces=0,
            last_stable_weight=0.0,
            last_base_weight=0.0,
            weights=[],
        )
        svc.update(biz, ButtonState(),
                    parse_ok=True, comm_ok=False,
                    exception_text="测试异常")

        d = self._ui_data(spy)
        assert d.status.parse.text == "解析正常"
        assert d.status.parse.style == Styles.GREEN
        assert d.status.comm.text == "通讯等待"
        assert d.status.comm.style == Styles.GRAY
        assert d.status.exception.text == "测试异常"
        assert d.status.exception.style == Styles.RED

    def test_weight_none_shows_dashes(self, qapp):
        svc = UIService()
        spy = QSignalSpy(svc.ui_changed)

        biz = BizResult(
            added=False,
            abnormal_high=False,
            abnormal_low=False,
            state=BizState.ZERO,
            delta=0.0,
            avg_weight=0.0,
            tol_high=0.0,
            tol_low=0.0,
            total_pieces=0,
            last_stable_weight=0.0,
            last_base_weight=0.0,
            weights=[],
        )
        svc.update(biz, ButtonState(), actual_weight=None)

        d = self._ui_data(spy)
        assert d.actual_weight == "-----"
