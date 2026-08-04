# app/core/csv_writer.py
from __future__ import annotations

import csv
import datetime
import threading
from pathlib import Path
from typing import Any, TextIO


class CsvWriter:
    """按日切分的 CSV 写入器，线程安全。"""

    def __init__(
        self, folder_path: Path, header: tuple[str, ...] = ("时间", "列1", "列2")
    ) -> None:
        self.folder: Path = folder_path
        self.folder.mkdir(parents=True, exist_ok=True)

        self.header: tuple[str, ...] = header

        self.file: TextIO | None = None
        self.writer: Any = None
        self.filepath: Path | None = None
        self.current_date: datetime.date | None = None
        self.lock: threading.RLock = threading.RLock()

    def _open_new_file(self) -> None:
        """打开当日 CSV（不存在则新建并写表头）。"""
        today = datetime.date.today()
        filename = f"log_{today.strftime('%Y%m%d')}.csv"

        self.filepath = self.folder / filename
        new_file = not self.filepath.exists()

        self.file = open(self.filepath, "a", newline="", encoding="utf-8-sig")
        self.writer = csv.writer(self.file)

        if new_file:
            self.writer.writerow(self.header)

        self.current_date = today

    def _ensure_file(self) -> None:
        """若未打开或已跨日，则切换到当日日志文件。"""
        with self.lock:
            today = datetime.date.today()

            if self.file is None:
                self._open_new_file()
                return

            if today != self.current_date:
                self.close()
                self._open_new_file()

    def write(self, timestamp: str, col1: str, col2: str) -> None:
        """写入一行并 flush。"""
        self._ensure_file()

        try:
            if self.writer is None or self.file is None:
                raise RuntimeError("日志文件未打开")
            self.writer.writerow([timestamp, col1, col2])
            self.file.flush()
        except Exception as e:
            raise RuntimeError(f"写日志失败：{e}") from e

    def close(self) -> None:
        """关闭当前打开的日志文件。"""
        with self.lock:
            if self.file:
                self.file.close()
                self.file = None
                self.writer = None
