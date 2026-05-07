# app/services/serial_service.py

from PySide6.QtCore import QObject, QTimer, Signal

from app.core.serial import SerialCommunication


class SerialService(QObject):
    """
    SerialService is responsible for:
    - Managing serial port open/close
    - Listening to data from the underlying SerialCommunication
    - Emitting the data_received signal (to the Controller)
    - Automatically handling input timeout (disconnection detection)
    - No dependency on UI, Controller, or business logic
    """

    data_received = Signal(str)  # raw serial data
    timeout_detected = Signal()  # timeout signal (Controller decides how to handle)
    error_occurred = Signal(str)

    def __init__(self, timeout_millis: int):
        super().__init__()

        self.serial = SerialCommunication()
        self.timeout_millis = timeout_millis

        # timeout detection timer
        self.timer = QTimer()
        self.timer.timeout.connect(self._on_timeout)

        # forward underlying serial data as a service signal
        self.serial.data_received.connect(self._on_raw_data)

    # ============================================================
    # Open / Close serial port
    # ============================================================
    def open(self, port: str, baud: int) -> None:
        self.serial.open(port, baud)
        self.timer.start(self.timeout_millis)

    def close(self):
        try:
            self.timer.stop()
            self.serial.close()
        except Exception as e:
            self.error_occurred.emit(str(e))

    # ============================================================
    # Serial data entry point
    # ============================================================
    def _on_raw_data(self, raw: str):
        self.timer.start(self.timeout_millis)
        self.data_received.emit(raw)

    def _on_timeout(self):
        self.timeout_detected.emit()
