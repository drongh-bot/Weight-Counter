# app/core/serial.py
import logging

from PySide6.QtCore import QIODevice, QObject, Signal
from PySide6.QtSerialPort import QSerialPort, QSerialPortInfo

logger = logging.getLogger(__name__)


class SerialCommunicationError(Exception):
    """Raised when a serial communication error occurs."""


class SerialCommunication(QObject):
    data_received = Signal(str)  # Signal emitted when data is received

    def __init__(self) -> None:
        super().__init__()
        self.serial: QSerialPort = QSerialPort(self)
        self.encoding: str = "utf-8"
        self.serial.readyRead.connect(self.on_ready_read)

    def open(
        self,
        port: str,
        baud_rate: int,
        data_bits: QSerialPort.DataBits = QSerialPort.DataBits.Data8,
        parity: QSerialPort.Parity = QSerialPort.Parity.NoParity,
        stop_bits: QSerialPort.StopBits = QSerialPort.StopBits.OneStop,
        flow_control: QSerialPort.FlowControl = QSerialPort.FlowControl.NoFlowControl,
    ) -> None:

        if self.serial.isOpen():
            raise SerialCommunicationError("串口已打开，请先关闭再重新打开。")

        ports = [p.portName() for p in QSerialPortInfo.availablePorts()]
        if port not in ports:
            raise SerialCommunicationError(f"错误，串口 {port} 没找到。")

        self.serial.setPortName(port)
        self.serial.setBaudRate(baud_rate)

        # Use configurable parameters (default: 8N1)
        self.serial.setDataBits(data_bits)
        self.serial.setParity(parity)
        self.serial.setStopBits(stop_bits)
        self.serial.setFlowControl(flow_control)

        if not self.serial.open(QIODevice.OpenModeFlag.ReadWrite):
            raise SerialCommunicationError(f"打开串口失败：{self.serial.errorString()}")

    def on_ready_read(self) -> None:
        while self.serial.canReadLine():
            raw = bytes(self.serial.readLine().data())
            try:
                text = raw.decode("utf-8")
                self.encoding = "utf-8"
            except UnicodeDecodeError:
                logger.warning("UTF-8解码失败, 回退GBK: %.20s", raw)
                text = raw.decode("gbk", errors="ignore")
                self.encoding = "gbk"
            self.data_received.emit(text)

    def write(self, data: str) -> None:
        if not self.serial.isOpen():
            raise SerialCommunicationError("串口未打开")
        self.serial.write(data.encode(self.encoding or "utf-8", errors="ignore"))

    def close(self) -> None:
        if self.serial.isOpen():
            self.serial.close()

    def is_open(self) -> bool:
        return self.serial.isOpen()
