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

    def __init__(self, timeout_millis: int) -> None:
        super().__init__()
        self.timeout_millis = timeout_millis
        self._port = QSerialPort(self)
        self._encoding = "utf-8"
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

        self._encoding = "utf-8"
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

    def _on_ready_read(self) -> None:
        while self._port.canReadLine():
            raw = bytes(self._port.readLine().data())
            try:
                text = raw.decode(self._encoding)
            except UnicodeDecodeError:
                logger.warning("解码失败, 回退GBK: %.20s", raw)
                text = raw.decode("gbk", errors="ignore")
                self._encoding = "gbk"
            self._timer.start(self.timeout_millis)
            self.data_received.emit(text)

    def _on_timeout(self) -> None:
        self.timeout_detected.emit()
