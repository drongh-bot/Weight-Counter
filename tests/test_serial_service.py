from PySide6.QtTest import QSignalSpy

from app.services.serial_service import SerialService


class TestSerialServiceLineAssembly:
    def test_lf_delimited(self, qapp):
        svc = SerialService(2000)
        spy = QSignalSpy(svc.data_received)
        svc._rx_buffer.extend(b"10.5\n")
        svc._emit_complete_lines()
        assert spy.count() == 1
        assert spy.at(0)[0] == "10.5"

    def test_cr_delimited(self, qapp):
        svc = SerialService(2000)
        spy = QSignalSpy(svc.data_received)
        svc._rx_buffer.extend(b"10.5\r")
        svc._emit_complete_lines()
        assert spy.count() == 1
        assert spy.at(0)[0] == "10.5"

    def test_crlf_delimited(self, qapp):
        svc = SerialService(2000)
        spy = QSignalSpy(svc.data_received)
        svc._rx_buffer.extend(b"10.5\r\n20.0\r\n")
        svc._emit_complete_lines()
        assert spy.count() == 2
        assert spy.at(0)[0] == "10.5"
        assert spy.at(1)[0] == "20.0"

    def test_partial_line_waits(self, qapp):
        svc = SerialService(2000)
        spy = QSignalSpy(svc.data_received)
        svc._rx_buffer.extend(b"10.")
        svc._emit_complete_lines()
        assert spy.count() == 0
        svc._rx_buffer.extend(b"5\n")
        svc._emit_complete_lines()
        assert spy.count() == 1
        assert spy.at(0)[0] == "10.5"
