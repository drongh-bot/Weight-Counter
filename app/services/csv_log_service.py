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

    def __init__(self) -> None:
        super().__init__()
        base = ResourceManager.get_external_root() / "log"
        self.production_writer: CsvWriter | None = CsvWriter(
            base / "production", ("Time", "Weight", "Total")
        )

        # log queue
        self._production_queue: queue.Queue = queue.Queue()

        self._is_active = True
        self._writer_thread = threading.Thread(
            target=self._worker_loop, name="LogWorker", daemon=True
        )
        self._writer_thread.start()

    # ============================================================
    # Background thread: unified log writer
    # ============================================================
    def _worker_loop(self) -> None:
        while True:
            try:
                item = self._production_queue.get(timeout=1.0)
            except queue.Empty:
                if not self._is_active:
                    break
                continue

            if item is None:
                self._production_queue.task_done()
                break

            timestamp, weight_str, total_str = item

            try:
                if self.production_writer:
                    self.production_writer.write(timestamp, weight_str, total_str)
            except Exception as e:
                self.error_occurred.emit(f"CSV write failed: {e}")
            finally:
                self._production_queue.task_done()

    # ============================================================
    # Utility: current time
    # ============================================================
    @staticmethod
    def _timestamp() -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ============================================================
    # Record production
    # ============================================================
    def record_production(self, weight: float, total: int) -> None:
        """
        weight: single-piece weight (last piece)
        total: current total count
        """
        if not self._is_active:
            return

        try:
            self._production_queue.put((self._timestamp(), f"{weight:.3f}", str(total)))
        except Exception as e:
            self.error_occurred.emit(f"Production write failed: {e}")

    # ============================================================
    # Safe shutdown (called on program exit)
    # ============================================================
    def close(self) -> None:
        """Ensure background thread exits safely without log loss"""

        # 1. Idempotency guard: prevent double close
        if not self._is_active:
            return

        # 2. Stop accepting new items
        self._is_active = False

        # 3. Wait for all queued items to be written to disk
        self._production_queue.join()

        # 4. Inject sentinel to unblock worker and trigger exit
        self._production_queue.put_nowait(None)

        # 5. Wait for worker thread to exit
        self._writer_thread.join(timeout=3.0)

        # 6. Close writer
        try:
            if self.production_writer:
                self.production_writer.close()
        except Exception as e:
            logger.error("关闭日志失败: %s", e)

        # 7. Prevent accidental writes after close
        self.production_writer = None
