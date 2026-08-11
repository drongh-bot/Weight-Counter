# app/services/csv_log_service.py
import logging
import queue
import threading
from datetime import datetime

from PySide6.QtCore import QObject, Signal

from app.core.csv_writer import CsvWriter
from app.core.resource_manager import ResourceManager

logger = logging.getLogger(__name__)

# (时间, 重量, 总件数)；None 表示「可以收工了」
_ProductionItem = tuple[str, str, str] | None


class CsvLogService(QObject):
    """把生产记录写到 CSV，不卡住界面。

    计件线程只往队列里丢一条；后台线程慢慢写文件。
    退出时先把队列里剩下的写完，再关文件。
    """

    error_occurred = Signal(str)

    def __init__(self) -> None:
        """打开生产日志，拉起后台写线程。"""
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
        """后台循环：有记录就写；收到收工信号或已停用且队列空则退出。"""
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
        """当前时间，写成日志里的时间列。"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def record_production(
        self, weight: float, total: int, decimal_places: int
    ) -> None:
        """记一笔生产：最新单重 + 当前总件数（只入队，马上返回）。"""
        if not self._is_active:
            return

        try:
            places = max(0, int(decimal_places))
            weight_str = f"{weight:.{places}f}"
            self._production_queue.put((self._timestamp(), weight_str, str(total)))
        except Exception as e:
            self.error_occurred.emit(f"生产记录入队失败：{e}")

    def close(self) -> None:
        """退出时调用：等队列写完，通知后台收工，再关日志文件。"""
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
