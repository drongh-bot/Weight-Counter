from app.services.serial_service import SerialService


class TestSerialServiceDecode:
    def test_decode_ascii_utf8(self, qapp):
        svc = SerialService(2000, encoding="utf-8")
        assert svc._decode_line(b"10.5 kg\n") == "10.5 kg\n"

    def test_decode_drops_invalid_utf8(self, qapp):
        svc = SerialService(2000, encoding="utf-8")
        assert svc._decode_line(b"N?\t\x02\xff\xfeZ\n") is None

    def test_decode_drops_blank(self, qapp):
        svc = SerialService(2000, encoding="utf-8")
        assert svc._decode_line(b"\r\n") is None

    def test_decode_gbk_when_configured(self, qapp):
        svc = SerialService(2000, encoding="gbk")
        raw = "重量".encode("gbk") + b"\n"
        assert svc._decode_line(raw) == "重量\n"

    def test_invalid_encoding_name_drops_line(self, qapp):
        svc = SerialService(2000, encoding="not-a-codec")
        assert svc._decode_line(b"10.0\n") is None
