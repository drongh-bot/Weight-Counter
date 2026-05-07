# app/services/log_service.py
import queue
import threading
from datetime import datetime

from PySide6.QtCore import QObject, Signal

from app.core.logger import Logger
from app.core.resource_manager import ResourceManager


class LogService(QObject):
    """
    Production-grade async log service:
    - Main thread / API callers only enqueue, no IO
    - Background thread handles all writes, avoiding GUI blocking
    - Supports safe shutdown (no log loss)
    - Supports sentinel mechanism (Poison Pill)
    - Supports queue.get(timeout) to prevent thread deadlock
    """

    log_error_occurred = Signal(str)

    def __init__(self):
        super().__init__()
        base = ResourceManager.get_external_root() / "log"
        # three log types
        self.event_logger = Logger(base / "event", ("Time", "Event", "Details"))
        self.error_logger = Logger(base / "error", ("Time", "Error", "Details"))
        self.production_logger = Logger(base / "production", ("Time", "Weight", "Total"))

        # log queue
        self.queue = queue.Queue()

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

                if log_type == "event" and self.event_logger:
                    self.event_logger.write(timestamp, col1, col2)

                elif log_type == "error" and self.error_logger:
                    self.error_logger.write(timestamp, col1, col2)

                elif log_type == "production" and self.production_logger:
                    self.production_logger.write(timestamp, col1, col2)

                self.queue.task_done()

            except Exception as e:
                # auto-queued, thread-safe
                self.log_error_occurred.emit(f"Log write failed: {e}")

    # ============================================================
    # Utility: current time
    # ============================================================
    def _timestamp(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ============================================================
    # Event log
    # ============================================================
    def log_event(self, msg: str, extra: str = "") -> None:
        if not self.running:
            return
        self.queue.put(("event", self._timestamp(), msg, extra))

    # ============================================================
    # Error log
    # ============================================================
    def log_error(self, error: Exception, extra: str = "") -> None:
        if not self.running:
            return
        self.queue.put(("error", self._timestamp(), f"{type(error).__name__}: {error}", extra))

    # ============================================================
    # Production log (based on PieceCounter properties)
    # ============================================================
    def log_production(self, weight: float, total: int) -> None:
        """
        weight: single-piece weight (last piece)
        total: current total count
        """
        if not self.running:
            return

        try:
            self.queue.put(("production", self._timestamp(), f"{weight:.3f}", str(total)))
        except Exception as e:
            self.log_error_occurred.emit(f"Production log write failed: {e}")

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

        # 5. Close all loggers
        try:
            if self.event_logger:
                self.event_logger.close()
            if self.error_logger:
                self.error_logger.close()
            if self.production_logger:
                self.production_logger.close()
        except Exception:
            pass

        # 6. Prevent accidental writes after close
        self.event_logger = None
        self.error_logger = None
        self.production_logger = None
