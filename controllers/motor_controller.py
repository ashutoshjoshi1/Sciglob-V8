from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QGroupBox, QLabel, QComboBox, QPushButton, QLineEdit, QGridLayout
from serial.tools import list_ports

from drivers.motor import MotorConnectThread, send_move_command

class MotorController(QObject):
    status_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.groupbox = QGroupBox("Motor")
        self.groupbox.setObjectName("motorGroup")
        layout = QGridLayout()

        # Bold labels for important elements
        port_label = QLabel("COM:")
        port_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(port_label, 0, 0)
        
        self.port_combo = QComboBox()
        self.port_combo.setEditable(True)
        ports = [p.device for p in list_ports.comports()]
        self.port_combo.addItems(ports or [f"COM{i}" for i in range(1, 10)])
        layout.addWidget(self.port_combo, 0, 1)
        
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.toggle_connection) # Changed
        layout.addWidget(self.connect_btn, 0, 2)

        # Add preset angle dropdown with bold label
        preset_label = QLabel("Preset (°):")
        preset_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(preset_label, 1, 0)
        
        self.angle_preset = QComboBox()
        # Add angles from 0 to 360 in 30 degree increments
        self.angle_preset.addItems([str(i) for i in range(0, 361, 30)])
        self.angle_preset.currentTextChanged.connect(self.preset_selected)
        layout.addWidget(self.angle_preset, 1, 1)
        
        # Keep the custom angle input with bold label
        custom_label = QLabel("Custom (°):")
        custom_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(custom_label, 2, 0)
        
        self.angle_input = QLineEdit()
        self.angle_input.setFixedWidth(60)
        layout.addWidget(self.angle_input, 2, 1)
        
        self.move_btn = QPushButton("Move")
        self.move_btn.setEnabled(False)
        self.move_btn.clicked.connect(self.move)
        layout.addWidget(self.move_btn, 2, 2)

        self.groupbox.setLayout(layout)
        self._connected = False
        self.serial = None
        self.current_angle_deg = None # Initialize current angle state

        # If configured port is provided, select and auto-connect
        if parent is not None and hasattr(parent, 'config'):
            cfg_port = parent.config.get("motor")
            if cfg_port:
                self.port_combo.setCurrentText(cfg_port)
                self.connect()

    def toggle_connection(self):
        """Toggles the connection state."""
        if not self._connected:
            self.connect()
        else:
            self.disconnect()

    def connect(self):
        if self._connected: # Should not happen if toggle_connection is used correctly
            return
        port = self.port_combo.currentText().strip()
        self.connect_btn.setEnabled(False)
        self.connect_btn.setText("Connecting...")
        self.status_signal.emit(f"Motor: Connecting to {port}...")
        thread = MotorConnectThread(port, parent=self) # Assuming MotorConnectThread handles its own errors and emits msg
        thread.result_signal.connect(self._on_connect)
        thread.start()

    def _on_connect(self, ser, baud, msg): # baud parameter seems unused by MotorController itself
        self.status_signal.emit(msg) # Display message from connect thread (success or failure)
        if ser: # Successfully connected
            self.serial = ser
            self._connected = True
            self.move_btn.setEnabled(True)
            self.connect_btn.setText("Disconnect")
            self.status_signal.emit(f"Motor connected on {ser.port}.") # More specific success message
            self.move_to(0)  # Move to 0 degrees on successful connection
        else: # Connection failed
            self._connected = False
            self.move_btn.setEnabled(False)
            self.connect_btn.setText("Connect") # Reset button text
        self.connect_btn.setEnabled(True) # Re-enable button in both cases

    def disconnect(self):
        """Disconnects from the motor serial port."""
        if self.serial and self.serial.is_open:
            try:
                self.serial.close()
                self.status_signal.emit("Motor disconnected.")
            except Exception as e:
                self.status_signal.emit(f"Motor: Error closing serial port: {e}")

        self._connected = False
        self.serial = None # Clear the serial object

        self.connect_btn.setText("Connect")
        self.connect_btn.setEnabled(True)
        self.move_btn.setEnabled(False)
        # Optionally, reset current angle display here if desired
        # self.current_angle_deg = None # Or some default
        # self.angle_input.setText("")

    def preset_selected(self, angle_text):
        """Handle selection from the preset angle dropdown"""
        self.angle_input.setText(angle_text)
        if self._connected:
            self.move()

    def move(self):
        """Move to the angle specified in the angle input field"""
        try:
            angle = int(self.angle_input.text().strip())
            self.move_to(angle)
        except ValueError:
            self.status_signal.emit("Invalid angle")

    def move_to(self, angle):
        """Move to the specified angle"""
        if not self._connected:
            self.status_signal.emit("Motor not connected")
            return False
        
        try:
            # First update the angle input field
            if hasattr(self, 'angle_input'): # Should always exist
                self.angle_input.setText(str(angle))
            
            # Disable move buttons during operation
            self.move_btn.setEnabled(False)
            self.angle_preset.setEnabled(False)

            # Convert angle to motor steps (100 steps per degree)
            # Assuming this conversion (angle * 100) is correct for the specific motor hardware
            motor_steps = int(angle * 100)
            
            ok = False
            if self.serial:
                # Note: If send_move_command is blocking and takes significant time,
                # it would be better to run it in a separate thread to keep the UI responsive.
                # For now, assuming it's acceptably fast for direct call.
                ok = send_move_command(self.serial, motor_steps)
                
                if ok:
                    self.current_angle_deg = angle # Update state upon successful command
                    self.status_signal.emit(f"Motor: Moved to {angle}°")
                else:
                    # If move failed, current_angle_deg remains the old value.
                    # Or set to None if position becomes uncertain: self.current_angle_deg = None
                    self.status_signal.emit(f"Motor: Failed to move to {angle}° (No ACK or other error)")
            else:
                self.status_signal.emit("Motor: Serial connection not available")
            
            # Re-enable move buttons
            self.move_btn.setEnabled(True)
            self.angle_preset.setEnabled(True)
            return ok

        except Exception as e:
            self.status_signal.emit(f"Motor: Error moving: {str(e)}")
            # Ensure buttons are re-enabled in case of exception during the move process
            if hasattr(self, 'move_btn') and self.move_btn: # Check if UI element still exists
                self.move_btn.setEnabled(True)
            if hasattr(self, 'angle_preset') and self.angle_preset: # Check if UI element still exists
                self.angle_preset.setEnabled(True)
            return False

    def is_connected(self):
        return self._connected



