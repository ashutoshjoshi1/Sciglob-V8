from PyQt5.QtCore import QObject, QTimer, pyqtSignal, Qt
from PyQt5.QtWidgets import QGroupBox, QLabel, QVBoxLayout, QHBoxLayout, QPushButton
from drivers.thp_sensor import read_thp_sensor_data

class THPController(QObject):
    status_signal = pyqtSignal(str)

    def __init__(self, port, parent=None):
        super().__init__(parent)
        self.port = port
        self.groupbox = QGroupBox("THP Sensor")
        self.groupbox.setObjectName("thpGroup")
        
        # Use vertical layout for more compact display
        layout = QVBoxLayout()
        layout.setSpacing(2)  # Reduce spacing
        
        # Top row with port and reconnect button
        top_row = QHBoxLayout()
        
        port_label = QLabel(f"Port: {port}")
        port_label.setStyleSheet("font-weight: bold;")
        top_row.addWidget(port_label)
        
        reconnect_btn = QPushButton("Reconnect")
        reconnect_btn.setMaximumWidth(80)
        reconnect_btn.clicked.connect(self.reconnect)
        top_row.addWidget(reconnect_btn)
        
        layout.addLayout(top_row)
        
        # Readings in a compact format with larger font
        self.readings_label = QLabel("Temp: -- °C | Humidity: -- % | Pressure: -- hPa")
        self.readings_label.setStyleSheet("font-size: 11pt; font-weight: bold;")
        self.readings_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.readings_label)
        
        self.groupbox.setLayout(layout)
        
        self._connected = False # Initialize connection state flag
        self.latest = {
            "temperature": 0.0,
            "humidity": 0.0,
            "pressure": 0.0
        }
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_data)
        self.timer.start(3000) # Start periodic updates
        self._update_data() # Initial data read attempt

    def _update_data(self):
        try:
            data = read_thp_sensor_data(self.port) # Assuming this handles port open/close
            if data:
                self.latest = data
                self.readings_label.setText(
                    f"Temp: {data['temperature']:.1f} °C | "
                    f"Humidity: {data['humidity']:.1f} % | "
                    f"Pressure: {data['pressure']:.1f} hPa"
                )
                if not self._connected: # If was previously disconnected
                    self.status_signal.emit(f"THP sensor connected on {self.port}")
                self._connected = True
            else:
                if self._connected: # If was previously connected
                    self.status_signal.emit(f"THP sensor read failed/disconnected on port {self.port}")
                self.readings_label.setText(f"Sensor not responding on {self.port}")
                self._connected = False
        except Exception as e:
            if self._connected: # If was previously connected
                self.status_signal.emit(f"THP sensor error: {e}")
            self.readings_label.setText(f"Sensor error on {self.port}")
            self._connected = False

    def get_latest(self):
        return self.latest

    def is_connected(self):
        return self._connected # Use the internal flag

    def reconnect(self):
        """Try to read data from the THP sensor again."""
        self.status_signal.emit(f"THP: Attempting to read from {self.port}...")
        self._update_data() # This already updates status and UI based on success/failure
        if self._connected:
            self.status_signal.emit(f"THP: Reconnected/Read successful on {self.port}")
        # else: # _update_data would have emitted a failure status
            # self.status_signal.emit(f"THP: Reconnect/Read failed on {self.port}")
        return self._connected

    def disconnect(self):
        """Stops periodic updates for the THP sensor."""
        if self.timer.isActive():
            self.timer.stop()
        self._connected = False
        self.readings_label.setText("THP updates stopped.")
        self.status_signal.emit(f"THP sensor updates stopped for port {self.port}.")






