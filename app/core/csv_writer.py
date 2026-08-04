# app/core/csv_writer.py
from __future__ import annotations

import csv
import datetime
import threading
from pathlib import Path
from typing import Any, TextIO


class CsvWriter:
    """按日切分的 CSV 写入器；同一实例上的 write/close 线程安全。"""

    def __init__(
        self, folder_path: Path, header: tuple[str, ...] = ("时间", "列1", "列2")
    ) -> None:
        self._folder: Path = folder_path
        self._folder.mkdir(parents=True, exist_ok=True)
        self._header: tuple[str, ...] = header

        self._file: TextIO | None = None
        self._writer: Any = None
        self._filepath: Path | None = None
        self._current_date: datetime.date | None = None
        self._lock: threading.RLock = threading.RLock()

    def _open_new_file(self) -> None:
        """打开当日 CSV（不存在则新建并写表头）。调用方须已持锁。"""
        today = datetime.date.today()
        self._filepath = self._folder / f"log_{today.strftime('%Y%m%d')}.csv"
        new_file = not self._filepath.exists()

        self._file = open(self._filepath, "a", newline="", encoding="utf-8-sig")
        self._writer = csv.writer(self._file)

        if new_file:
            self._writer.writerow(self._header)

        self._current_date = today

    def _close_file(self) -> None:
        """关闭当前文件句柄。调用方须已持锁。"""
        if self._file is not None:
            self._file.close()
            self._file = None
            self._writer = None

    def _ensure_file(self) -> None:
        """若未打开或已跨日，则切换到当日日志文件。调用方须已持锁。"""
        today = datetime.date.today()
        if self._file is None:
            self._open_new_file()
            return
        if today != self._current_date:
            self._close_file()
            self._open_new_file()

    def write(self, *cells: str) -> None:
        """写入一行并 flush；列数须与表头一致。"""
        if len(cells) != len(self._header):
            raise ValueError(
                f"列数不符：期望 {len(self._header)}，实际 {len(cells)}"
            )
        with self._lock:
            self._ensure_file()
            if self._writer is None or self._file is None:
                raise RuntimeError("日志文件未打开")
            try:
                self._writer.writerow(cells)
                self._file.flush()
            except Exception as e:
                raise RuntimeError(f"写日志失败：{e}") from e

    def close(self) -> None:
        """关闭当前打开的日志文件。"""
        with self._lock:
            self._close_file()
