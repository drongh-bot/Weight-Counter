# app/services/csv_log_service.py
import logging
import queue
import threading
from datetime import datetime

from PySide6.QtCore import QObject, Signal

from app.core.csv_writer import CsvWriter
from app.core.resource_manager import ResourceManager
from app.models.formatting import format_weight

logger = logging.getLogger(__name__)

# (时间, 重量, 总件数)；None 表示「可以收工了」
_ProductionItem = tuple[str, str, str] | None

# 退出时最多等写线程多久；写卡住也不能把进程一起拖死
_CLOSE_TIMEOUT_SECONDS = 3.0


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
        """后台循环：有记录就写；收到 None 哨兵后退出。"""
        while True:
            item = self._production_queue.get()

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

    def record_production(self, weight: float, total: int, decimal_places: int) -> None:
        """记一笔生产：最新单重 + 当前总件数（只入队，马上返回）。"""
        if not self._is_active:
            return

        try:
            places = max(0, int(decimal_places))
            weight_str = format_weight(weight, places)
            self._production_queue.put((self._timestamp(), weight_str, str(total)))
        except Exception as e:
            self.error_occurred.emit(f"生产记录入队失败：{e}")

    def close(self) -> None:
        """退出时调用：等后台把队列写完再收工，最多等 ``_CLOSE_TIMEOUT_SECONDS`` 秒。

        哨兵 ``None`` 排在所有记录之后，所以线程退出即代表队列已写空，
        不必再 ``queue.join()``（那个没有超时，写线程卡住会让退出也一起卡死）。
        """
        if not self._is_active:
            return

        self._is_active = False
        self._production_queue.put_nowait(None)

        self._writer_thread.join(timeout=_CLOSE_TIMEOUT_SECONDS)
        if self._writer_thread.is_alive():
            # 线程还在写：不能把文件关掉/置空，否则它下一帧就写到 None 上
            logger.error(
                "日志线程 %.0f 秒内没退出，跳过关闭日志文件",
                _CLOSE_TIMEOUT_SECONDS,
            )
            return

        writer, self._production_writer = self._production_writer, None
        if writer is None:
            return
        try:
            writer.close()
        except Exception as e:
            logger.error("关闭日志失败: %s", e)
