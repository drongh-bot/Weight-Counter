# app/services/csv_log_service.py
import logging
import queue
import threading
from datetime import datetime

from PySide6.QtCore import QObject, Signal

from app.core.csv_writer import CsvWriter
from app.core.resource_manager import ResourceManager

logger = logging.getLogger(__name__)

# (时间, 重量, 总件数)；None 为关闭哨兵
_ProductionItem = tuple[str, str, str] | None


class CsvLogService(QObject):
    """
    异步 CSV 记录服务：
    - 主线程 / API 调用方仅入队，不做 IO
    - 后台线程统一写入，避免阻塞 GUI
    - 支持安全关闭（不丢记录）
    - 支持哨兵机制（Poison Pill）
    - 支持 queue.get(timeout) 防止线程死锁
    """

    error_occurred = Signal(str)

    def __init__(self) -> None:
        """启动后台写线程与生产日志 Writer。"""
        super().__init__()
        base = ResourceManager.get_external("log")
        self._production_writer: CsvWriter | None = CsvWriter(
            base / "production", ("时间", "重量", "总件数")
        )

        self._production_queue: queue.Queue[_ProductionItem] = queue.Queue()

        self._is_active: bool = True
        self._writer_thread: threading.Thread = threading.Thread(
            target=self._worker_loop, name="LogWorker", daemon=True
        )
        self._writer_thread.start()

    def _worker_loop(self) -> None:
        """后台线程：从队列取记录并写入 CSV。"""
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
                if self._production_writer:
                    self._production_writer.write(timestamp, weight_str, total_str)
            except Exception as e:
                self.error_occurred.emit(f"CSV 写入失败：{e}")
            finally:
                self._production_queue.task_done()

    @staticmethod
    def _timestamp() -> str:
        """当前时间戳字符串。"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def record_production(self, weight: float, total: int) -> None:
        """入队一条生产记录（weight=最新单重，total=当前总件数）。"""
        if not self._is_active:
            return

        try:
            self._production_queue.put((self._timestamp(), f"{weight:.3f}", str(total)))
        except Exception as e:
            self.error_occurred.emit(f"生产记录入队失败：{e}")

    def close(self) -> None:
        """安全关闭：排空队列、结束后台线程、关闭文件。"""
        if not self._is_active:
            return

        self._is_active = False
        self._production_queue.join()
        self._production_queue.put_nowait(None)
        self._writer_thread.join(timeout=3.0)

        try:
            if self._production_writer:
                self._production_writer.close()
        except Exception as e:
            logger.error("关闭日志失败: %s", e)

        self._production_writer = None
