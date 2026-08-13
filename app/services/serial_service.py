# app/services/serial_service.py
import logging

from PySide6.QtCore import QIODevice, QObject, QTimer, Signal
from PySide6.QtSerialPort import QSerialPort, QSerialPortInfo

logger = logging.getLogger(__name__)


class SerialCommunicationError(Exception):
    """串口通信错误。"""


class SerialService(QObject):
    """串口 I/O + 输入超时检测。唯一 data_received 出口。"""

    data_received = Signal(str)
    timeout_detected = Signal()
    error_occurred = Signal(str)

    def __init__(self, timeout_millis: int, encoding: str = "utf-8") -> None:
        super().__init__()
        self.timeout_millis = timeout_millis
        self._encoding = encoding or "utf-8"
        self._port = QSerialPort(self)
        self._port.readyRead.connect(self._on_ready_read)

        self._timer = QTimer()
        self._timer.timeout.connect(self._on_timeout)

    def open(self, port: str, baud: int) -> None:
        """打开串口并启动超时计时器。"""
        if self._port.isOpen():
            raise SerialCommunicationError("串口已打开，请先关闭再重新打开。")

        ports = [p.portName() for p in QSerialPortInfo.availablePorts()]
        if port not in ports:
            raise SerialCommunicationError(f"错误，串口 {port} 没找到。")

        self._port.setPortName(port)
        self._port.setBaudRate(baud)
        self._port.setDataBits(QSerialPort.DataBits.Data8)
        self._port.setParity(QSerialPort.Parity.NoParity)
        self._port.setStopBits(QSerialPort.StopBits.OneStop)
        self._port.setFlowControl(QSerialPort.FlowControl.NoFlowControl)

        if not self._port.open(QIODevice.OpenModeFlag.ReadWrite):
            raise SerialCommunicationError(
                f"打开串口失败：{self._port.errorString()}"
            )

        self._timer.start(self.timeout_millis)

    def close(self) -> None:
        """关闭串口并停止计时器。"""
        try:
            self._timer.stop()
            if self._port.isOpen():
                self._port.close()
        except Exception as e:
            logger.error("串口关闭失败: %s", e)
            self.error_occurred.emit(str(e))

    def _decode_line(self, raw: bytes) -> str | None:
        """按固定编码解码一行；空行或非法字节返回 None（丢弃，不切换编码）。"""
        if not raw.strip():
            return None
        try:
            return raw.decode(self._encoding)
        except (UnicodeDecodeError, LookupError):
            logger.debug("串口非文本行，已丢弃: %r", raw[:32])
            return None

    def _on_ready_read(self) -> None:
        while self._port.canReadLine():
            raw = bytes(self._port.readLine().data())
            text = self._decode_line(raw)
            if text is None:
                continue
            self._timer.start(self.timeout_millis)
            self.data_received.emit(text)

    def _on_timeout(self) -> None:
        self.timeout_detected.emit()
