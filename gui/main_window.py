import sys
import os
import json
import numpy as np
import cv2

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QGridLayout, QSplitter,
    QLabel, QPushButton, QStatusBar, QMessageBox, QHBoxLayout, QGroupBox,
    QApplication, QComboBox, QFileDialog, QSpinBox, QDoubleSpinBox, QLineEdit
)
from PyQt5.QtCore import QTimer, Qt, QDateTime
from PyQt5.QtGui import QImage, QPixmap

from controllers.motor_controller import MotorController
from controllers.filterwheel_controller import FilterWheelController
from controllers.imu_controller import IMUController
from controllers.spectrometer_controller import SpectrometerController
from controllers.temp_controller import TempController
from controllers.thp_controller import THPController

from gui.components.data_logger import DataLogger
from gui.components.routine_manager import RoutineManager
from gui.components.camera_manager import CameraManager
from gui.components.ui_manager import UIManager

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Mini ROBOHyPO")
        
        # Get screen size and set window size proportionally
        screen_rect = QApplication.desktop().availableGeometry()
        screen_width, screen_height = screen_rect.width(), screen_rect.height()
        
        # Set window size to 90% of screen size
        window_width = int(screen_width * 0.9)
        window_height = int(screen_height * 0.9)
        self.resize(window_width, window_height)
        
        # Set minimum size proportional to screen size
        min_width = min(1280, int(screen_width * 0.7))
        min_height = min(800, int(screen_height * 0.7))
        self.setMinimumSize(min_width, min_height)
        
        # Add flag to prevent overlapping updates
        self._updating = False
        self._hardware_changing = False
        self._integration_changing = False
        
        # Initialize UI manager
        self.ui_manager = UIManager(self)
        self.ui_manager.setup_ui_style()
        
        # Load configuration
        self.config = {}
        try:
            config_path = os.path.join(os.path.dirname(__file__), "..", "hardware_config.json")
            with open(config_path, 'r') as cfg_file:
                self.config = json.load(cfg_file)
        except Exception as e:
            print(f"Config load error: {e}")

        self.latest_data = {}
        self.pixel_counts = []
        
        # Initialize components
        self.data_logger = DataLogger(self)
        self.routine_manager = RoutineManager(self)
        self.camera_manager = CameraManager(self)
        
        # Initialize hardware controllers
        self.init_controllers()
        
        # Set up the main UI layout
        self.setup_ui()
        
        # Initialize hardware state tracking variables
        self._last_motor_angle = 0
        self._last_filter_position = 0
        
        # Timer for hardware state change detection
        self._hardware_change_timer = QTimer(self)
        self._hardware_change_timer.timeout.connect(self._hardware_change_timeout)
        
        # Timer for updating UI indicators
        self._indicator_timer = QTimer(self)
        self._indicator_timer.timeout.connect(self._update_indicators)
        self._indicator_timer.start(2000)  # Update every 2 seconds
        
        # Set up status bar
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Application initialized")

    def init_controllers(self):
        """Initialize hardware controllers"""
        controller_initializers = {
            "THP Sensor": lambda: THPController(port=self.config.get("thp_sensor", "COM8"), parent=self),
            "Spectrometer": lambda: SpectrometerController(parent=self),
            "Temperature Controller": lambda: TempController(parent=self),
            "Motor Controller": lambda: MotorController(parent=self),
            "Filter Wheel": lambda: FilterWheelController(parent=self),
            "IMU": lambda: IMUController(parent=self)
        }

        controller_attributes = {
            "THP Sensor": "thp_ctrl",
            "Spectrometer": "spec_ctrl",
            "Temperature Controller": "temp_ctrl",
            "Motor Controller": "motor_ctrl",
            "Filter Wheel": "filter_ctrl",
            "IMU": "imu_ctrl"
        }

        for name, initializer in controller_initializers.items():
            attr_name = controller_attributes[name]
            try:
                controller = initializer()
                setattr(self, attr_name, controller)
                if hasattr(controller, 'status_signal'):
                    controller.status_signal.connect(self.statusBar().showMessage)
                    controller.status_signal.connect(self.handle_status_message)
                # Attempt to connect or check status if applicable, may vary by controller
                if hasattr(controller, 'connect') and callable(getattr(controller, 'connect')):
                    if not controller.connect(): # Assuming connect returns True on success
                        self.statusBar().showMessage(f"{name}: Initial connection failed.")
                        self.handle_status_message(f"{name}: Initial connection failed.")
                    else:
                        self.statusBar().showMessage(f"{name}: Initialized successfully.")
                        self.handle_status_message(f"{name}: Initialized successfully.")
                elif hasattr(controller, 'is_connected') and callable(getattr(controller, 'is_connected')):
                    if controller.is_connected():
                         self.statusBar().showMessage(f"{name}: Initialized and connected.")
                         self.handle_status_message(f"{name}: Initialized and connected.")
                    else:
                        # For controllers like Spectrometer that auto-connect or have complex init
                        # their own status signals might be more appropriate.
                        # This provides a fallback status.
                        self.statusBar().showMessage(f"{name}: Initialized, connection status pending or failed.")
                        self.handle_status_message(f"{name}: Initialized, connection status pending or failed.")
                else:
                    self.statusBar().showMessage(f"{name}: Initialized (connection status unknown).")
                    self.handle_status_message(f"{name}: Initialized (connection status unknown).")

            except Exception as e:
                setattr(self, attr_name, None) # Ensure attribute exists but is None
                error_msg = f"{name}: Initialization failed - {e}"
                self.statusBar().showMessage(error_msg)
                self.handle_status_message(error_msg)
                # Optionally, create a dummy controller or handle this in UI updates
                print(f"Error initializing {name}: {e}")


    def setup_ui(self):
        """Set up the main UI layout"""
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        
        # Create a main horizontal splitter for the entire layout
        main_splitter = QSplitter(Qt.Horizontal)
        self.main_splitter = main_splitter  # Store reference for resizeEvent
        
        # Left side - Spectrometer (give it most of the space)
        main_splitter.addWidget(self.spec_ctrl.groupbox)
        
        # Right side - All other controls in a vertical layout
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(5)  # Reduce spacing between elements
        
        # Top section - Camera
        self.cam_group = QGroupBox("Camera Feed")
        self.cam_group.setObjectName("cameraGroup")
        cam_layout = QVBoxLayout(self.cam_group)
        self.cam_label = QLabel("Camera feed will appear here")
        self.cam_label.setAlignment(Qt.AlignCenter)
        self.cam_label.setMinimumHeight(240)  # Increase minimum height
        self.cam_label.setStyleSheet("background-color: #1a1a1a; color: #e0e0e0; font-size: 12pt; font-weight: bold; border-radius: 5px;")
        cam_layout.addWidget(self.cam_label)
        right_layout.addWidget(self.cam_group)
        
        # Initialize camera
        self.camera_manager.init_camera()
        
        # Middle section - Routine controls
        self.routine_group = QGroupBox("Routine Control")
        self.routine_group.setObjectName("routineGroup")
        routine_layout = QVBoxLayout(self.routine_group)
        
        # Preset dropdown
        preset_layout = QHBoxLayout()
        preset_label = QLabel("Preset:")
        preset_label.setStyleSheet("font-weight: bold;")
        preset_layout.addWidget(preset_label)
        
        self.preset_combo = QComboBox()
        self.preset_combo.addItem("Custom...")
        self.preset_combo.addItems(["Standard Scan", "Dark Reference", "White Reference", "Filter Sequence", "Temperature Test"])
        self.preset_combo.currentIndexChanged.connect(self.preset_selected)
        preset_layout.addWidget(self.preset_combo)
        
        routine_layout.addLayout(preset_layout)
        
        # Load and Run buttons
        routine_btn_layout = QHBoxLayout()
        self.load_routine_btn = QPushButton("Load File")
        self.load_routine_btn.setStyleSheet("font-weight: bold; font-size: 11pt;")
        self.load_routine_btn.clicked.connect(self.routine_manager.load_routine_file)
        routine_btn_layout.addWidget(self.load_routine_btn)
        
        self.run_routine_btn = QPushButton("Run Code")
        self.run_routine_btn.setStyleSheet("font-weight: bold; font-size: 11pt;")
        self.run_routine_btn.setEnabled(False)
        self.run_routine_btn.clicked.connect(self.routine_manager.run_routine)
        routine_btn_layout.addWidget(self.run_routine_btn)
        routine_layout.addLayout(routine_btn_layout)
        
        self.routine_status = QLabel("No routine loaded")
        self.routine_status.setStyleSheet("font-size: 11pt; font-weight: bold;")
        self.routine_status.setAlignment(Qt.AlignCenter)
        routine_layout.addWidget(self.routine_status)
        right_layout.addWidget(self.routine_group)
        
        # Bottom section - 2x2 grid for controllers
        controllers_grid = QGridLayout()
        controllers_grid.setSpacing(5)  # Reduce spacing

        # Temperature controller (top row, spans both columns)
        self.temp_ctrl.widget.setMaximumHeight(180)  # Increased from 150 to 180
        controllers_grid.addWidget(self.temp_ctrl.widget, 0, 0, 1, 2)  # Span both columns

        # Motor controller (middle left)
        self.motor_ctrl.groupbox.setMaximumHeight(200)  # Limit height
        controllers_grid.addWidget(self.motor_ctrl.groupbox, 1, 0)

        # Filter wheel controller (middle right)
        self.filter_ctrl.groupbox.setMaximumHeight(200)  # Limit height
        controllers_grid.addWidget(self.filter_ctrl.groupbox, 1, 1)

        # IMU controller (bottom left)
        self.imu_ctrl.groupbox.setMaximumHeight(200)  # Limit height
        controllers_grid.addWidget(self.imu_ctrl.groupbox, 2, 0)

        # THP controller (bottom right)
        self.thp_ctrl.groupbox.setMaximumHeight(200)  # Limit height
        controllers_grid.addWidget(self.thp_ctrl.groupbox, 2, 1)
        
        right_layout.addLayout(controllers_grid)
        
        # Add the right panel to the main splitter
        main_splitter.addWidget(right_panel)
        
        # Set stretch factors - give spectrometer much more space
        main_splitter.setStretchFactor(0, 4)  # Spectrometer gets 4 parts
        main_splitter.setStretchFactor(1, 1)  # Right panel gets 1 part
        
        main_layout.addWidget(main_splitter)
        
        # Start camera update timer
        self.camera_timer = QTimer(self)
        self.camera_timer.timeout.connect(self.camera_manager.update_camera_feed)
        self.camera_timer.start(100)  # 10 fps

    def preset_selected(self, index):
        """Handle preset selection from dropdown"""
        if index == 0:  # Custom
            return
        
        preset_name = self.preset_combo.currentText()
        self.routine_manager.load_preset_routine(preset_name)

    def toggle_data_saving(self):
        """Toggle continuous data saving on/off"""
        is_saving = self.data_logger.toggle_data_saving()
        
        # Update UI based on saving state
        if is_saving:
            self.statusBar().showMessage("Data saving started")
            
            # Get current integration time from spectrometer controller
            integration_time_ms = 1000  # Default 1 second
            if self.spec_ctrl and hasattr(self.spec_ctrl, 'current_integration_time_us'):
                integration_time_ms = self.spec_ctrl.current_integration_time_us
            else:
                self.statusBar().showMessage("Spectrometer controller not available, using default integration time for saving.")
            
            # Ensure minimum interval of 100ms
            collection_interval = max(100, int(integration_time_ms))
            
            # Start data collection timer - collect at integration time rate
            self.data_timer = QTimer(self)
            self.data_timer.timeout.connect(self.data_logger.collect_data_sample)
            self.data_timer.start(collection_interval)
            
            # Start data saving timer - save at integration time rate plus a small buffer
            save_interval = int(integration_time_ms + 200)  # Add 200ms buffer for processing
            self.save_timer = QTimer(self)
            self.save_timer.timeout.connect(self.data_logger.save_continuous_data)
            self.save_timer.start(save_interval)
            
            # Store the current timers for later adjustment
            self.data_logger.collection_interval = collection_interval
            self.data_logger.save_interval = save_interval
            
            # Update button text if it exists
            if self.spec_ctrl and hasattr(self.spec_ctrl, 'toggle_btn'):
                self.spec_ctrl.toggle_btn.setText("Stop Saving")
        else:
            self.statusBar().showMessage("Data saving stopped")
            
            # Stop timers
            if hasattr(self, 'data_timer'):
                self.data_timer.stop()
            if hasattr(self, 'save_timer'):
                self.save_timer.stop()
            
            # Update button text if it exists
            if self.spec_ctrl and hasattr(self.spec_ctrl, 'toggle_btn'):
                self.spec_ctrl.toggle_btn.setText("Start Saving")

    def collect_data_sample(self):
        """Collect a data sample for averaging, with pause on hardware state changes"""
        if not (hasattr(self, 'continuous_saving') and self.continuous_saving and
                  self.spec_ctrl and hasattr(self.spec_ctrl, 'intens') and self.spec_ctrl.intens):
            if hasattr(self, 'continuous_saving') and self.continuous_saving:
                 # Only show message if saving is active but spec_ctrl is the issue
                if not self.spec_ctrl:
                    self.statusBar().showMessage("Spectrometer not available for data collection.", 2000)
            return
        
        # Check for hardware state changes
        current_motor_angle = 0
        if hasattr(self.motor_ctrl, "current_angle_deg"):
            current_motor_angle = self.motor_ctrl.current_angle_deg
        
        current_filter_pos = self.filter_ctrl.get_position()
        if current_filter_pos is None:
            current_filter_pos = getattr(self.filter_ctrl, "current_position", 0)
        
        # Detect hardware state changes
        motor_changed = abs(current_motor_angle - self._last_motor_angle) > 0.5
        filter_changed = current_filter_pos != self._last_filter_position
        
        if (motor_changed or filter_changed) and not self._hardware_changing:
            # Hardware state has changed, pause data collection
            self._hardware_changing = True
            self.statusBar().showMessage("Hardware state changed - pausing data collection for 2 seconds...")
            self.handle_status_message(f"Pausing data collection: {'Motor moved' if motor_changed else 'Filter changed'}")
            
            # Update tracking variables
            self._last_motor_angle = current_motor_angle
            self._last_filter_position = current_filter_pos
            
            # Start timer to resume data collection after 2 seconds
            self._hardware_change_timer.start(2000)  # 2 second pause
            return
        
        # If hardware is still changing, don't collect data
        if self._hardware_changing:
            return
        
        # Collect data sample
        self.data_logger.collect_data_sample()

    def _hardware_change_timeout(self):
        """Resume data collection after hardware state change pause"""
        self._hardware_changing = False
        self._hardware_change_timer.stop()
        self.statusBar().showMessage("Resuming data collection after hardware state change")
        self.handle_status_message("Resuming data collection")

    def _update_indicators(self):
        """Update groupbox titles with connection status (green if connected, red if not)"""
        for ctrl, title, ok_fn in [
            (self.motor_ctrl, "Motor", self.motor_ctrl.is_connected),
            (self.filter_ctrl, "Filter Wheel", self.filter_ctrl.is_connected),
            (self.imu_ctrl, "IMU", self.imu_ctrl.is_connected),
            (self.spec_ctrl, "Spectrometer", self.spec_ctrl.is_ready),
            (self.temp_ctrl, "Temperature", lambda: hasattr(self.temp_ctrl, 'tc')),
            (self.thp_ctrl, "THP Sensor", lambda: self.thp_ctrl.is_connected() if self.thp_ctrl else False)
        ]:
            if ctrl is None: # Controller might have failed to initialize
                col = "#aaaaaa" # Grey out if controller is None
                # Try to get the groupbox/widget via a known attribute name if ctrl is None
                # This part is tricky as we don't have a direct way to get the UI element if ctrl is None
                # For now, we'll skip updating title if ctrl is None, or find a way if UI elements are stored elsewhere
                # A better approach would be to ensure groupboxes are always created and stored, even if controller fails.
                # However, current setup links groupbox to controller instance.
                # Let's assume for now that if ctrl is None, its UI wasn't fully added or should be visually distinct.
                # We can try to find the groupbox if it's stored with a known name, e.g. self.spec_ctrl_gb
                # For this iteration, if ctrl is None, we just log it and don't try to update its UI to avoid errors.
                print(f"Info: Controller for '{title}' is None, skipping indicator update.")
                continue

            col = "#4caf50" if ok_fn() else "#f44336"  # Green if connected, red if not
            gb = ctrl.groupbox if hasattr(ctrl, 'groupbox') else ctrl.widget
            
            if gb is None: # If the groupbox/widget itself is None
                print(f"Info: UI element for '{title}' is None, skipping indicator update.")
                continue

            gb.setTitle(f"● {title}")
            gb.setStyleSheet(f"""
                QGroupBox#{gb.objectName()}::title {{
                    color: {col};
                    font-weight: bold;
                    font-size: 12pt;
                    position: relative;
                    top: -2px;  /* Move title up by 2 pixels */
                }}
                
                QGroupBox#{gb.objectName()} {{
                    margin-top: 1.5ex;  /* Increased margin-top */
                    padding-top: 1ex;   /* Increased padding-top */
                }}
            """)

    def handle_status_message(self, message: str):
        """Log hardware state changes with level tags."""
        if not hasattr(self.data_logger, 'log_file') or not self.data_logger.log_file:
            return
            
        msg_lower = message.lower()
        # Determine severity level
        if ("fail" in msg_lower or "error" in msg_lower or "no response" in msg_lower or "cannot" in msg_lower):
            level = "ERROR"
        elif ("no ack" in msg_lower or "invalid" in msg_lower or "not connected" in msg_lower or "not ready" in msg_lower):
            level = "WARNING"
        else:
            level = "INFO"
            
        ts = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
        log_line = f"{ts} [{level}] {message}\n"
        
        try:
            self.data_logger.log_file.write(log_line)
            self.data_logger.log_file.flush() # Ensure log is written to OS buffer
        except Exception as e:
            print(f"Log write error: {e}")

    def resizeEvent(self, event):
        """Handle window resize events to adjust UI elements"""
        super().resizeEvent(event)
        
        # Adjust camera label size based on window size
        if hasattr(self, 'cam_label'):
            # Set camera label height proportional to window height
            cam_height = max(180, int(self.height() * 0.2))
            self.cam_label.setMinimumHeight(cam_height)
        
        # Adjust splitter proportions
        if hasattr(self, 'main_splitter'):
            window_width = self.width()
            # Adjust splitter based on window width
            if window_width < 1600:
                # For smaller screens, give more space to controls
                self.main_splitter.setSizes([int(window_width * 0.6), int(window_width * 0.4)])
            else:
                # For larger screens, give more space to spectrometer
                self.main_splitter.setSizes([int(window_width * 0.7), int(window_width * 0.3)])
        
        # Update camera feed to fit new size
        if hasattr(self, 'camera_manager'):
            self.camera_manager.update_camera_feed()

    def closeEvent(self, event):
        """Handle window close event"""
        # Stop spectrometer if active
        if hasattr(self, 'spec_ctrl') and self.spec_ctrl is not None:
            try:
                if hasattr(self.spec_ctrl, 'measure_active') and self.spec_ctrl.measure_active:
                    self.statusBar().showMessage("Stopping spectrometer before exit...")
                    self.spec_ctrl.stop()
                    # Wait briefly for the spectrometer to stop
                    QTimer.singleShot(500, lambda: self.cleanup_and_close(event))
                    event.ignore()  # Temporarily ignore the close event
                    return
            except Exception as e:
                print(f"Error stopping spectrometer: {e}")
        
        self.cleanup_and_close(event)

    def cleanup_and_close(self, event):
        """Clean up resources and close the application"""
        # Clean up resources
        if hasattr(self, 'data_logger') and hasattr(self.data_logger, 'continuous_saving') and self.data_logger.continuous_saving:
            self.toggle_data_saving()
        
        if hasattr(self.data_logger, 'csv_file') and self.data_logger.csv_file:
            self.data_logger.csv_file.close()
        if hasattr(self.data_logger, 'log_file') and self.data_logger.log_file:
            self.data_logger.log_file.close()
        
        # Release camera resources if initialized
        if hasattr(self, 'camera_manager'):
            self.camera_manager.release_camera()
        
        # Call the parent class closeEvent
        # event.accept() # This will be handled by shutdown_resources or main.py exit logic

    def shutdown_resources(self):
        """Clean up all resources before application exit."""
        self.statusBar().showMessage("Shutting down resources...")
        print("MainWindow: Starting shutdown_resources...")

        # 1. Stop all timers
        for timer_attr in ['_hardware_change_timer', '_indicator_timer', 'camera_timer',
                           'data_timer', 'save_timer']: # data_timer and save_timer might be from DataLogger
            if hasattr(self, timer_attr):
                timer = getattr(self, timer_attr)
                if timer is not None and timer.isActive():
                    timer.stop()
                    print(f"MainWindow: Stopped timer {timer_attr}")

        # If data_timer and save_timer are part of DataLogger, they should be stopped there.
        # Let's assume DataLogger has its own shutdown method or handles this in toggle_data_saving.
        # For now, the above will attempt to stop them if they are attributes of MainWindow.

        # 2. Stop continuous data saving if active
        # This will call DataLogger._stop_data_saving() which closes its files.
        if hasattr(self, 'data_logger') and self.data_logger is not None:
            if hasattr(self.data_logger, 'continuous_saving') and self.data_logger.continuous_saving:
                try:
                    print("MainWindow: Stopping continuous data saving via toggle_data_saving...")
                    # toggle_data_saving in MainWindow calls self.data_logger.toggle_data_saving(),
                    # which in turn calls self.data_logger._stop_data_saving().
                    # It also stops MainWindow's data_timer and save_timer.
                    self.toggle_data_saving()
                except Exception as e:
                    print(f"Error during toggle_data_saving in shutdown: {e}")
            # Ensure files are closed even if continuous_saving was somehow false but files were open
            # DataLogger._stop_data_saving() handles setting files to None.
            # If DataLogger has a direct method to ensure files are closed, call that.
            # For now, relying on the continuous_saving flag being accurate.
            # If not saving, _stop_data_saving in DataLogger would have been called already.
            # Consider adding a more explicit data_logger.ensure_files_closed() if issues persist.

        # 3. Stop spectrometer
        if hasattr(self, 'spec_ctrl') and self.spec_ctrl is not None:
            try:
                if hasattr(self.spec_ctrl, 'measure_active') and self.spec_ctrl.measure_active:
                    print("MainWindow: Stopping spectrometer measurement...")
                    self.spec_ctrl.stop()
                if hasattr(self.spec_ctrl, 'disconnect'): # Assuming a disconnect method
                    print("MainWindow: Disconnecting spectrometer...")
                    self.spec_ctrl.disconnect()
            except Exception as e:
                print(f"Error stopping/disconnecting spectrometer: {e}")

        # 4. Release camera
        if hasattr(self, 'camera_manager'):
            try:
                print("MainWindow: Releasing camera...")
                self.camera_manager.release_camera()
            except Exception as e:
                print(f"Error releasing camera: {e}")

        # 5. Close/disconnect other hardware controllers
        controllers_to_close = [
            ('thp_ctrl', 'THP Controller'),
            ('temp_ctrl', 'Temperature Controller'),
            ('motor_ctrl', 'Motor Controller'),
            ('filter_ctrl', 'Filter Wheel Controller'),
            ('imu_ctrl', 'IMU Controller')
        ]
        for ctrl_attr, name in controllers_to_close:
            if hasattr(self, ctrl_attr):
                controller = getattr(self, ctrl_attr)
                if controller is not None:
                    if hasattr(controller, 'disconnect'): # Prefer disconnect
                        try:
                            print(f"MainWindow: Disconnecting {name}...")
                            controller.disconnect()
                        except Exception as e:
                            print(f"Error disconnecting {name}: {e}")
                    elif hasattr(controller, 'close'): # Fallback to close
                        try:
                            print(f"MainWindow: Closing {name}...")
                            controller.close()
                        except Exception as e:
                            print(f"Error closing {name}: {e}")

        # 6. Close DataLogger files (log and CSV) - This is now handled by step 2.
        # The call to self.toggle_data_saving() (if continuous saving was active)
        # triggers self.data_logger.toggle_data_saving(), which calls _stop_data_saving() in DataLogger.
        # _stop_data_saving() in DataLogger closes the files and sets them to None.
        # So, explicit closing here is redundant and potentially problematic if files are already None.
        print("MainWindow: DataLogger files should be closed by DataLogger._stop_data_saving if necessary.")

        print("MainWindow: shutdown_resources completed.")
        self.statusBar().showMessage("Resources shut down.")
