# tests/test_csv_writer.py
"""CsvWriter：按日切分、表头只写一次、列数校验、跨日切换。"""

import datetime as dt
from pathlib import Path

import pytest

from app.core import csv_writer as csv_writer_module
from app.core.csv_writer import CsvWriter


def _only_csv(folder: Path) -> Path:
    files = list(folder.glob("log_*.csv"))
    assert len(files) == 1
    return files[0]


class TestWrite:
    def test_first_write_creates_file_with_header(self, tmp_path):
        w = CsvWriter(tmp_path, ("时间", "重量"))
        w.write("2026-09-27", "10.0")
        w.close()

        content = _only_csv(tmp_path).read_text(encoding="utf-8-sig")
        assert content.splitlines() == ["时间,重量", "2026-09-27,10.0"]

    def test_header_written_only_once(self, tmp_path):
        w = CsvWriter(tmp_path, ("a", "b"))
        w.write("1", "2")
        w.write("3", "4")
        w.close()

        lines = _only_csv(tmp_path).read_text(encoding="utf-8-sig").splitlines()
        assert lines[0] == "a,b"  # 表头只有一行
        assert len(lines) == 3

    def test_wrong_column_count_raises(self, tmp_path):
        w = CsvWriter(tmp_path, ("a", "b"))
        with pytest.raises(ValueError, match="列数不符"):
            w.write("only-one")

    def test_utf8_sig_bom_written(self, tmp_path):
        """Excel 打开中文不乱码靠 BOM。"""
        w = CsvWriter(tmp_path, ("说明",))
        w.write("中文")
        w.close()

        assert _only_csv(tmp_path).read_bytes().startswith(b"\xef\xbb\xbf")

    def test_write_after_close_reopens(self, tmp_path):
        """close 只是关句柄；下次 write 要能自动重开（_ensure_file 的分支）。"""
        w = CsvWriter(tmp_path, ("a",))
        w.write("1")
        w.close()
        w.write("2")
        w.close()

        lines = _only_csv(tmp_path).read_text(encoding="utf-8-sig").splitlines()
        assert lines == ["a", "1", "2"]


class TestDailyRotation:
    """跨日切文件 —— 用假日期驱动，不依赖真的等到明天。"""

    @staticmethod
    def _fake_date(monkeypatch, first: dt.date):
        """把 csv_writer 里的 datetime.date.today() 换成受控的假日期。"""

        class FakeDate(dt.date):
            current = first

            @classmethod
            def today(cls):
                return cls.current

        monkeypatch.setattr(csv_writer_module.datetime, "date", FakeDate)
        return FakeDate

    def test_rolls_over_to_new_file_at_midnight(self, tmp_path, monkeypatch):
        FakeDate = self._fake_date(monkeypatch, dt.date(2026, 1, 1))
        w = CsvWriter(tmp_path, ("a",))
        w.write("day1")
        FakeDate.current = dt.date(2026, 1, 2)  # 过零点
        w.write("day2")
        w.close()

        names = sorted(p.name for p in tmp_path.glob("log_*.csv"))
        assert names == ["log_20260101.csv", "log_20260102.csv"]
        assert "day1" in (tmp_path / "log_20260101.csv").read_text(encoding="utf-8-sig")
        assert "day2" in (tmp_path / "log_20260102.csv").read_text(encoding="utf-8-sig")

    def test_same_day_appends_to_same_file(self, tmp_path, monkeypatch):
        self._fake_date(monkeypatch, dt.date(2026, 1, 1))
        w = CsvWriter(tmp_path, ("a",))
        w.write("one")
        w.write("two")
        w.close()

        assert len(list(tmp_path.glob("log_*.csv"))) == 1
