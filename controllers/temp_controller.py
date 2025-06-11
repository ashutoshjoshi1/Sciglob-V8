from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from PyQt5.QtWidgets import QGroupBox, QGridLayout, QLabel, QLineEdit, QPushButton, QComboBox, QDoubleSpinBox, QHBoxLayout
from serial.tools import list_ports

from drivers.tc36_25_driver import TC36_25

class TempController(QObject):
    status_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        # Group box for Temperature Controller
        self.widget = QGroupBox("Temperature Controller")
        self.widget.setObjectName("tempGroup")
        layout = QGridLayout()
        layout.setVerticalSpacing(8)  # Increase vertical spacing between rows
        
        # Use bold labels and larger fonts for important elements
        port_label = QLabel("COM Port:")
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
        
        # Current temperature with bold label and larger font
        temp_label = QLabel("Current TEC:")
        temp_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(temp_label, 1, 0)
        
        self.temp_display = QLabel("-- °C")
        self.temp_display.setStyleSheet("font-size: 12pt; font-weight: bold;")
        layout.addWidget(self.temp_display, 1, 1)
        
        # Add auxiliary temperature display
        aux_temp_label = QLabel("Spec Temp:")
        aux_temp_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(aux_temp_label, 2, 0)
        
        self.aux_temp_display = QLabel("-- °C")
        self.aux_temp_display.setStyleSheet("font-size: 12pt; font-weight: bold;")
        layout.addWidget(self.aux_temp_display, 2, 1)

    # Placeholder for _update_ui_connected and _update_ui_disconnected, will be added with connect/disconnect logic
    # def _update_ui_connected(self): ...
    # def _update_ui_disconnected(self): ...
        
        # Setpoint with bold label and more intuitive layout
        setpoint_label = QLabel("Set Temperature:")
        setpoint_label.setStyleSheet("font-weight: bold; font-size: 11pt;")
        layout.addWidget(setpoint_label, 3, 0)
        
        # Use a horizontal layout for the setpoint controls
        setpoint_layout = QHBoxLayout()
        setpoint_layout.setContentsMargins(0, 5, 0, 0)  # Add some top margin
        
        self.setpoint_spin = QDoubleSpinBox()
        self.setpoint_spin.setRange(15, 40)
        self.setpoint_spin.setValue(20.0)
        self.setpoint_spin.setSingleStep(0.5)
        self.setpoint_spin.setSuffix(" °C")
        self.setpoint_spin.setEnabled(False)
        self.setpoint_spin.setStyleSheet("font-size: 11pt;")
        self.setpoint_spin.setMinimumWidth(100)
        setpoint_layout.addWidget(self.setpoint_spin)
        
        self.set_btn = QPushButton("Set")
        self.set_btn.setEnabled(False)
        self.set_btn.clicked.connect(self.set_temp)
        self.set_btn.setStyleSheet("font-weight: bold; font-size: 11pt;")
        setpoint_layout.addWidget(self.set_btn)
        
        layout.addLayout(setpoint_layout, 3, 1, 1, 2)
        
        self.widget.setLayout(layout)

        # Initialize state variables
        self._connected = False
        self.tc = None # Will hold the TC36_25 driver instance
        self.timer = QTimer(self) # QTimer for periodic UI updates via _upd
        self.timer.timeout.connect(self._upd)
        self._temp_read_timer = None # For the threading.Timer used in _upd's timeout mechanism
        self._temp_read_timeout = False # Flag to indicate if a read timeout occurred
        self._current_temperature_value = 0.0
        self._aux_temperature_value = 0.0

        # Auto-connect if configured
        # Default UI state will be set after attempting connection or if no port is configured.
        if parent is not None and hasattr(parent, 'config'):
            cfg_port = parent.config.get("temp_controller")
            if cfg_port:
                self.port_combo.setCurrentText(cfg_port)
                self.connect() # Call the refactored connect method
            else:
                self._update_ui_disconnected() # Use the new UI helper
        else:
            self._update_ui_disconnected() # Use the new UI helper

    def _update_ui_connected(self):
        self.connect_btn.setText("Disconnect")
        self.connect_btn.setEnabled(True)
        self.setpoint_spin.setEnabled(True)
        self.set_btn.setEnabled(True)
        # temp_display and aux_temp_display will be updated by _upd

    def _update_ui_disconnected(self):
        self.connect_btn.setText("Connect")
        self.connect_btn.setEnabled(True) # Allow to try connecting again
        self.setpoint_spin.setEnabled(False)
        self.set_btn.setEnabled(False)
        self.temp_display.setText("-- °C")
        self.aux_temp_display.setText("-- °C")
        self._current_temperature_value = 0.0 # Reset state
        self._aux_temperature_value = 0.0   # Reset state

    # Removed _update_ui_disconnected_initial as _update_ui_disconnected serves the same purpose.

    def set_preset_temp(self, temp):
        """Set temperature to a preset value (kept for backward compatibility)"""
        if not self._connected: # Check internal connected flag
            self.status_signal.emit("TC: Not connected")
            return
        
        self.setpoint_spin.setValue(temp)
        self.set_temp()

    def set_temp(self):
        """Set the temperature setpoint"""
        if not self._connected or self.tc is None:
            self.status_signal.emit("TC: Not connected, cannot set temperature.")
            return
        try:
            t = self.setpoint_spin.value()
            self.tc.set_setpoint(t)
            self.status_signal.emit(f"TC: Setpoint set to {t:.1f}°C")
        except Exception as e:
            self.status_signal.emit(f"TC: Failed to set temperature: {e}")

    def _upd(self):
        """Update the current temperature display with timeout protection"""
        if not self._connected or self.tc is None:
            # This case should ideally not happen if timer is stopped on disconnect
            return

        try:
            # Set a timeout for temperature reading
            # Ensure _temp_read_timer is only created and started if not already running
            if self._temp_read_timer is None or not self._temp_read_timer.is_alive():
                from threading import Timer # Keep import here if only used here
                self._temp_read_timer = Timer(0.5, self._timeout_temp_read) # 0.5s timeout
                self._temp_read_timer.daemon = True # Ensure thread doesn't prevent app exit
                self._temp_read_timer.start()
                
            # Read primary temperature
            current = self.tc.get_temperature() # This call might block

            # If get_temperature() succeeded, cancel the timeout timer
            if self._temp_read_timer is not None and self._temp_read_timer.is_alive():
                self._temp_read_timer.cancel()
            self._temp_read_timer = None # Reset timer instance
            self._temp_read_timeout = False # Reset timeout flag

            self._current_temperature_value = current # Update state variable
            self.temp_display.setText(f"{self._current_temperature_value:.2f} °C")
            
            # Read auxiliary temperature
            try:
                aux_temp = self.tc.get_auxiliary_temperature()
                self._aux_temperature_value = aux_temp # Update state variable
                self.aux_temp_display.setText(f"{self._aux_temperature_value:.2f} °C")
            except Exception as e_aux:
                self.aux_temp_display.setText("-- °C")
                self._aux_temperature_value = 0.0 # Reset on error
                if not self._temp_read_timeout: # Don't spam if main read also timed out
                    self.status_signal.emit(f"TC: Aux temp read error: {e_aux}")
            
        except Exception as e_main:
            # This block is entered if tc.get_temperature() fails (excluding timeout handled by _timeout_temp_read)
            # Or if the timeout mechanism itself has an issue before tc.get_temperature()
            if not self._temp_read_timeout: # Check if timeout hasn't already handled this
                self.temp_display.setText("-- °C")
                self.aux_temp_display.setText("-- °C")
                self._current_temperature_value = 0.0
                self._aux_temperature_value = 0.0
                self.status_signal.emit(f"TC: Main temp read error: {e_main}")
            # If timeout occurred, _timeout_temp_read would have updated UI and emitted status.

    def _timeout_temp_read(self):
        """Called when temperature reading times out"""
        self._temp_read_timeout = True
        self.temp_display.setText("-- °C") # Update UI on timeout
        self.aux_temp_display.setText("-- °C")
        self._current_temperature_value = 0.0
        self._aux_temperature_value = 0.0
        self.status_signal.emit("TC: Temperature read timed out.")
        self._temp_read_timer = None # Clear timer instance

    @property
    def current_temp(self):
        # Current temperature reading from controller
        return self._current_temperature_value # Return internal state

    @property
    def setpoint(self):
        # Last set temperature (if known)
        try:
            return self.setpoint_spin.value() # UI is source of truth for setpoint
        except:
            return 0.0 # Default if UI element not available

    @property
    def auxiliary_temp(self):
        # Auxiliary temperature reading from controller
        return self._aux_temperature_value # Return internal state

    def is_connected(self):
        """Check if temperature controller is connected"""
        return self._connected # Use internal flag

    def toggle_connection(self):
        if not self._connected:
            self.connect()
        else:
            self.disconnect()

    def connect(self):
        """Connects to the temperature controller."""
        if self._connected:
            return

        port = self.port_combo.currentText().strip()
        self.status_signal.emit(f"TC: Connecting to {port}...")
        self.connect_btn.setEnabled(False) # Disable button during connection attempt
        self.connect_btn.setText("Connecting...")

        try:
            self.tc = TC36_25(port) # Attempt to connect to the hardware
            # Initialize hardware settings
            self.tc.enable_computer_setpoint()
            self.tc.power(True)
            
            self._connected = True # Set connected flag
            self.timer.start(1000) # Start QTimer for periodic updates via _upd
            self._update_ui_connected() # Update UI to connected state
            self.status_signal.emit(f"TC: Connected on {port}")
        except Exception as e:
            self.status_signal.emit(f"TC: Connection failed: {e}")
            self.tc = None # Ensure tc is None if connection failed
            self._connected = False
            self._update_ui_disconnected() # Update UI to disconnected state
        # finally: # Ensure button is re-enabled if not handled by _update_ui_...
            # self.connect_btn.setEnabled(True) # This is handled by _update_ui_...

    def disconnect(self):
        """Disconnects from the temperature controller."""
        self.status_signal.emit("TC: Disconnecting...")
        if self.timer.isActive(): # Stop the QTimer
            self.timer.stop()

        # Safely cancel the threading.Timer if it's active
        if self._temp_read_timer is not None: # Check if it exists
            if self._temp_read_timer.is_alive():
                self._temp_read_timer.cancel()
            self._temp_read_timer = None # Clear it

        if self.tc is not None: # If a TC driver instance exists
            try:
                self.tc.power(False) # Turn off power
                # Assuming TC36_25's __del__ or another method handles serial port closing.
                # If explicit close is needed for TC36_25 driver: self.tc.close()
                self.status_signal.emit("TC: Power turned off.")
            except Exception as e:
                self.status_signal.emit(f"TC: Error during power off/disconnect: {e}")

        self.tc = None # Release driver instance
        self._connected = False
        self._update_ui_disconnected() # Use helper to update UI
        self.status_signal.emit("TC: Disconnected.")
















