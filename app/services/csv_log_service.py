# app/services/csv_log_service.py
import logging
import queue
import threading
from datetime import datetime

from PySide6.QtCore import QObject, Signal

from app.core.csv_writer import CsvWriter
from app.core.resource_manager import ResourceManager

logger = logging.getLogger(__name__)


class CsvLogService(QObject):
    """
    Async CSV record service:
    - Main thread / API callers only enqueue, no IO
    - Background thread handles all writes, avoiding GUI blocking
    - Supports safe shutdown (no record loss)
    - Supports sentinel mechanism (Poison Pill)
    - Supports queue.get(timeout) to prevent thread deadlock
    """

    error_occurred = Signal(str)

    def __init__(self):
        super().__init__()
        base = ResourceManager.get_external_root() / "log"
        self.event_writer: CsvWriter | None = CsvWriter(base / "event", ("Time", "Event", "Details"))
        self.error_writer: CsvWriter | None = CsvWriter(base / "error", ("Time", "Error", "Details"))
        self.production_writer: CsvWriter | None = CsvWriter(base / "production", ("Time", "Weight", "Total"))

        # log queue
        self.queue: queue.Queue = queue.Queue()

        # background thread control
        self.running = True
        self.worker = threading.Thread(
            target=self._worker_loop, name="LogWorker", daemon=True
        )
        self.worker.start()

    # ============================================================
    # Background thread: unified log writer
    # ============================================================
    def _worker_loop(self) -> None:
        while True:
            try:
                # prevent get() from blocking indefinitely
                try:
                    item = self.queue.get(timeout=1.0)
                except queue.Empty:
                    if not self.running:
                        break  # queue empty and stopped -> safe exit
                    continue

                # sentinel: immediate exit
                if item is None:
                    break

                log_type, timestamp, col1, col2 = item

                if log_type == "event" and self.event_writer:
                    self.event_writer.write(timestamp, col1, col2)

                elif log_type == "error" and self.error_writer:
                    self.error_writer.write(timestamp, col1, col2)

                elif log_type == "production" and self.production_writer:
                    self.production_writer.write(timestamp, col1, col2)

                self.queue.task_done()

            except Exception as e:
                # auto-queued, thread-safe
                self.error_occurred.emit(f"CSV write failed: {e}")

    # ============================================================
    # Utility: current time
    # ============================================================
    def _timestamp(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ============================================================
    # Record event
    # ============================================================
    def record_event(self, msg: str, extra: str = "") -> None:
        if not self.running:
            return
        self.queue.put(("event", self._timestamp(), msg, extra))

    # ============================================================
    # Record error
    # ============================================================
    def record_error(self, error: Exception, extra: str = "") -> None:
        if not self.running:
            return
        self.queue.put(("error", self._timestamp(), f"{type(error).__name__}: {error}", extra))

    # ============================================================
    # Record production
    # ============================================================
    def record_production(self, weight: float, total: int) -> None:
        """
        weight: single-piece weight (last piece)
        total: current total count
        """
        if not self.running:
            return

        try:
            self.queue.put(("production", self._timestamp(), f"{weight:.3f}", str(total)))
        except Exception as e:
            self.error_occurred.emit(f"Production write failed: {e}")

    # ============================================================
    # Safe shutdown (called on program exit)
    # ============================================================
    def close(self) -> None:
        """Ensure background thread exits safely without log loss"""

        # 1. Idempotency guard: prevent double close
        if not self.running:
            return

        # 2. Stop background thread
        self.running = False

        # 3. Inject sentinel to unblock queue.get()
        self.queue.put_nowait(None)

        # 4. Wait for background thread to finish writing remaining logs
        self.worker.join(timeout=2.0)

        # 5. Close all writers
        try:
            if self.event_writer:
                self.event_writer.close()
            if self.error_writer:
                self.error_writer.close()
            if self.production_writer:
                self.production_writer.close()
        except Exception as e:
            logger.error("关闭日志失败: %s", e)

        # 6. Prevent accidental writes after close
        self.event_writer = None
        self.error_writer = None
        self.production_writer = None
