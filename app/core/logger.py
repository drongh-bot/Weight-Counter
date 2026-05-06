# app/core/logger.py
import csv
import datetime
import threading
from pathlib import Path
from typing import TextIO


class Logger:
    def __init__(
        self, folder_path: Path, header: tuple[str, ...] = ("时间", "列1", "列2")
    ) -> None:
        self.folder: Path = folder_path
        self.folder.mkdir(parents=True, exist_ok=True)

        self.header: tuple[str, ...] = header

        self.file: TextIO | None = None
        self.writer: csv.writer | None = None
        self.filepath: Path | None = None
        self.current_date: datetime.date | None = None
        self.lock: threading.Lock = threading.Lock()

    # ---------------------------------------------------------
    # Open CSV file (one per day)
    # ---------------------------------------------------------
    def _open_new_file(self) -> None:
        today = datetime.date.today()
        filename = f"log_{today.strftime('%Y%m%d')}.csv"

        self.filepath = self.folder / filename
        new_file = not self.filepath.exists()

        self.file = open(self.filepath, "a", newline="", encoding="utf-8-sig")
        self.writer = csv.writer(self.file)

        # Write common header
        if new_file:
            self.writer.writerow(self.header)

        self.current_date = today

    # ---------------------------------------------------------
    # Check if log file needs to be switched
    # ---------------------------------------------------------
    def _ensure_file(self) -> None:
        with self.lock:
            today = datetime.date.today()

            if self.file is None:
                self._open_new_file()
                return

            if today != self.current_date:
                self.close()
                self._open_new_file()

    # ---------------------------------------------------------
    # Write to CSV (generic three columns)
    # ---------------------------------------------------------
    def write(self, timestamp: str, col1: str, col2: str) -> None:
        self._ensure_file()

        try:
            self.writer.writerow([timestamp, col1, col2])
            self.file.flush()
        except Exception as e:
            raise RuntimeError(f"写日志失败：{e}") from e

    # ---------------------------------------------------------
    # Close file
    # ---------------------------------------------------------
    def close(self) -> None:
        if self.file:
            self.file.close()
            self.file = None
            self.writer = None

    # ---------------------------------------------------------
    # Context manager support
    # ---------------------------------------------------------
    def __enter__(self) -> "Logger":
        self._ensure_file()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
