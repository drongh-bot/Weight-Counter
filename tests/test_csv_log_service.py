from app.core.resource_manager import ResourceManager
from app.services.csv_log_service import CsvLogService


def _make_service(tmp_path, monkeypatch) -> CsvLogService:
    """把日志目录指到 tmp_path，别真往项目 log/ 里写。"""
    monkeypatch.setattr(
        ResourceManager, "get_external", staticmethod(lambda _rel: tmp_path)
    )
    return CsvLogService()


class TestCsvLogService:
    @staticmethod
    def _csv_files(tmp_path):
        """CsvWriter 会写到 日志目录/production/ 下。"""
        return list((tmp_path / "production").glob("*.csv"))

    def test_close_flushes_queued_records(self, tmp_path, monkeypatch):
        service = _make_service(tmp_path, monkeypatch)
        service.record_production(10.5, total=3, decimal_places=2)
        service.close()

        files = self._csv_files(tmp_path)
        assert len(files) == 1
        rows = files[0].read_text(encoding="utf-8-sig").splitlines()
        assert len(rows) == 2  # 表头 + 刚记的那一笔
        assert rows[1].split(",")[1:] == ["10.50", "3"]

    def test_close_is_idempotent(self, tmp_path, monkeypatch):
        """重复 close 不能抛，也不该再动已经收工的线程。"""
        service = _make_service(tmp_path, monkeypatch)
        service.close()
        service.close()

    def test_record_after_close_is_ignored(self, tmp_path, monkeypatch):
        service = _make_service(tmp_path, monkeypatch)
        service.close()
        service.record_production(1.0, total=1, decimal_places=2)

        assert self._csv_files(tmp_path) == []
