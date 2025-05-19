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

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
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
        
        # Set application-wide font with size relative to screen resolution
        app = QApplication.instance()
        font = app.font()
        base_font_size = max(9, min(12, int(screen_height / 100)))
        font.setPointSize(base_font_size)
        app.setFont(font)
        
        # Adjust stylesheet for responsive design
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{
                background-color: #1e1e1e;
                color: #e0e0e0;
            }}
            
            QGroupBox {{ 
                font-weight: bold; 
                font-size: {base_font_size + 1}pt;
                border: 1px solid #3a3a3a;
                border-radius: 5px;
                margin-top: 1.5ex;  /* Increased margin-top to make more room for title */
                padding-top: 1ex;   /* Increased padding-top to push content down */
                background-color: #252525;
            }}
            
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 8px;
                color: #e0e0e0;
                position: relative;
                top: -2px;  /* Move title up by 2 pixels */
            }}
            
            QLabel {{
                font-size: {base_font_size}pt;
                color: #e0e0e0;
            }}
            
            QPushButton {{
                font-size: {base_font_size}pt;
                padding: {max(4, int(base_font_size/2))}px {max(8, base_font_size)}px;
                background-color: #2d2d2d;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                color: #e0e0e0;
            }}
            
            QPushButton:hover {{
                background-color: #3a3a3a;
                border: 1px solid #4a4a4a;
            }}
            
            QPushButton:pressed {{
                background-color: #505050;
            }}
            
            QPushButton:disabled {{
                background-color: #2a2a2a;
                color: #707070;
                border: 1px solid #333333;
            }}
            
            QComboBox, QLineEdit, QSpinBox, QDoubleSpinBox {{
                font-size: {base_font_size}pt;
                padding: 4px;
                background-color: #2d2d2d;
                border: 1px solid #3a3a3a;
                border-radius: 3px;
                color: #e0e0e0;
            }}
            
            QComboBox:hover, QLineEdit:hover, QSpinBox:hover, QDoubleSpinBox:hover {{
                border: 1px solid #4a4a4a;
            }}
            
            QComboBox::drop-down {{
                border: 0px;
            }}
            
            QComboBox::down-arrow {{
                width: 14px;
                height: 14px;
            }}
            
            QSpinBox::up-button, QSpinBox::down-button,
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
                background-color: #3a3a3a;
                border: 1px solid #4a4a4a;
            }}
            
            QStatusBar {{
                font-size: {base_font_size}pt;
                background-color: #252525;
                color: #e0e0e0;
                border-top: 1px solid #3a3a3a;
            }}
            
            QTabWidget::pane {{
                border: 1px solid #3a3a3a;
                background-color: #252525;
            }}
            
            QTabBar::tab {{
                background-color: #2d2d2d;
                color: #e0e0e0;
                padding: 8px 12px;
                border: 1px solid #3a3a3a;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }}
            
            QTabBar::tab:selected {{
                background-color: #353535;
                border-bottom: none;
            }}
            
            QTabBar::tab:hover {{
                background-color: #3a3a3a;
            }}
            
            QSplitter::handle {{
                background-color: #3a3a3a;
            }}
            
            QScrollBar:vertical {{
                border: none;
                background-color: #2d2d2d;
                width: 10px;
                margin: 0px;
            }}
            
            QScrollBar::handle:vertical {{
                background-color: #505050;
                min-height: 20px;
                border-radius: 5px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background-color: #606060;
            }}
            
            QScrollBar:horizontal {{
                border: none;
                background-color: #2d2d2d;
                height: 10px;
                margin: 0px;
            }}
            
            QScrollBar::handle:horizontal {{
                background-color: #505050;
                min-width: 20px;
                border-radius: 5px;
            }}
            
            QScrollBar::handle:horizontal:hover {{
                background-color: #606060;
            }}
            
            QCheckBox {{
                color: #e0e0e0;
            }}
            
            QCheckBox::indicator {{
                width: 15px;
                height: 15px;
                background-color: #2d2d2d;
                border: 1px solid #3a3a3a;
                border-radius: 3px;
            }}
            
            QCheckBox::indicator:checked {{
                background-color: #4a86e8;
                border: 1px solid #4a86e8;
            }}
        """)
        
        self.config = {}
        try:
            config_path = os.path.join(os.path.dirname(__file__), "..", "hardware_config.json")
            with open(config_path, 'r') as cfg_file:
                self.config = json.load(cfg_file)
        except Exception as e:
            print(f"Config load error: {e}")

        self.latest_data = {}
        self.pixel_counts = []
        
        # Initialize log file attributes
        self.log_file = None
        self.csv_file = None
        self.continuous_saving = False
        
        # Create log directories if they don't exist
        self.log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
        self.csv_dir = os.path.join(os.path.dirname(__file__), "..", "data")
        os.makedirs(self.log_dir, exist_ok=True)
        os.makedirs(self.csv_dir, exist_ok=True)

        thp_port = self.config.get("thp_sensor", "COM8")
        self.thp_ctrl = THPController(port=thp_port, parent=self)
        self.thp_ctrl.status_signal.connect(self.statusBar().showMessage)

        self.setStatusBar(QStatusBar())

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        
        # Create a main horizontal splitter for the entire layout
        main_splitter = QSplitter(Qt.Horizontal)
        self.main_splitter = main_splitter  # Store reference for resizeEvent
        
        # Left side - Spectrometer (give it most of the space)
        self.spec_ctrl = SpectrometerController(parent=self)
        self.spec_ctrl.status_signal.connect(self.statusBar().showMessage)
        self.spec_ctrl.status_signal.connect(self.handle_status_message)
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
        self.camera = cv2.VideoCapture(0)
        if not self.camera.isOpened():
            self.statusBar().showMessage("Warning: Could not open camera")
        else:
            self.statusBar().showMessage("Camera initialized successfully")
        
        # Start camera update timer
        self.camera_timer = QTimer(self)
        self.camera_timer.timeout.connect(self.update_camera_feed)
        self.camera_timer.start(100)  # Update at 10fps instead of 30fps
        
        # Second section - Routine Code
        self.routine_group = QGroupBox("Routine Code")
        self.routine_group.setObjectName("routineGroup")
        routine_layout = QVBoxLayout(self.routine_group)

        # Add dropdown for preset routine code
        preset_layout = QHBoxLayout()
        preset_label = QLabel("Routine Code:")
        preset_label.setStyleSheet("font-weight: bold;")
        preset_layout.addWidget(preset_label)

        self.preset_combo = QComboBox()
        self.preset_combo.addItems(["Select Code", "SO", "FU", "RE", "SG"])
        self.preset_combo.setCurrentIndex(0)
        self.preset_combo.currentIndexChanged.connect(self.load_preset_schedule)
        preset_layout.addWidget(self.preset_combo)
        routine_layout.addLayout(preset_layout)

        # Custom routine code file loading
        routine_btn_layout = QHBoxLayout()
        self.load_routine_btn = QPushButton("Load Custom Code")
        self.load_routine_btn.setStyleSheet("font-weight: bold; font-size: 11pt;")
        self.load_routine_btn.clicked.connect(self.load_routine_file)
        routine_btn_layout.addWidget(self.load_routine_btn)

        self.run_routine_btn = QPushButton("Run Code")
        self.run_routine_btn.setStyleSheet("font-weight: bold; font-size: 11pt;")
        self.run_routine_btn.setEnabled(False)
        self.run_routine_btn.clicked.connect(self.run_routine)
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
        self.temp_ctrl = TempController(parent=self)
        self.temp_ctrl.status_signal.connect(self.statusBar().showMessage)
        self.temp_ctrl.status_signal.connect(self.handle_status_message)
        self.temp_ctrl.widget.setMaximumHeight(180)  # Increased from 150 to 180
        controllers_grid.addWidget(self.temp_ctrl.widget, 0, 0, 1, 2)  # Span both columns

        # Motor controller (middle left)
        self.motor_ctrl = MotorController(parent=self)
        self.motor_ctrl.status_signal.connect(self.statusBar().showMessage)
        self.motor_ctrl.status_signal.connect(self.handle_status_message)
        self.motor_ctrl.groupbox.setMaximumHeight(200)  # Limit height
        controllers_grid.addWidget(self.motor_ctrl.groupbox, 1, 0)

        # Filter wheel controller (middle right)
        self.filter_ctrl = FilterWheelController(parent=self)
        self.filter_ctrl.status_signal.connect(self.statusBar().showMessage)
        self.filter_ctrl.status_signal.connect(self.handle_status_message)
        self.filter_ctrl.groupbox.setMaximumHeight(200)  # Limit height
        controllers_grid.addWidget(self.filter_ctrl.groupbox, 1, 1)

        # IMU controller (bottom left)
        self.imu_ctrl = IMUController(parent=self)
        self.imu_ctrl.status_signal.connect(self.statusBar().showMessage)
        self.imu_ctrl.status_signal.connect(self.handle_status_message)
        self.imu_ctrl.groupbox.setMaximumHeight(200)  # Limit height
        controllers_grid.addWidget(self.imu_ctrl.groupbox, 2, 0)

        # THP controller (bottom right)
        thp_port = self.config.get("thp_sensor", "COM8")
        self.thp_ctrl = THPController(port=thp_port, parent=self)
        self.thp_ctrl.status_signal.connect(self.statusBar().showMessage)
        self.thp_ctrl.groupbox.setMaximumHeight(200)  # Limit height
        controllers_grid.addWidget(self.thp_ctrl.groupbox, 2, 1)
        
        right_layout.addLayout(controllers_grid)
        
        # Add the right panel to the main splitter
        main_splitter.addWidget(right_panel)
        
        # Set stretch factors - give spectrometer much more space
        main_splitter.setStretchFactor(0, 4)  # Spectrometer gets 4 parts
        main_splitter.setStretchFactor(1, 1)  # Right panel gets 1 part
        
        main_layout.addWidget(main_splitter)

        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self._update_indicators)
        self.status_timer.start(1000)
        self._update_indicators()

        self.save_data_timer = QTimer(self)
        self.save_data_timer.timeout.connect(self.save_continuous_data)

        # Add hardware state tracking for detecting changes
        self._last_motor_angle = 0
        self._last_filter_position = 0
        self._hardware_changing = False
        self._hardware_change_timer = QTimer(self)
        self._hardware_change_timer.setSingleShot(True)
        self._hardware_change_timer.timeout.connect(self._resume_after_hardware_change)

    def toggle_data_saving(self):
        if not self.continuous_saving:
            if self.csv_file:
                self.csv_file.close()
            if self.log_file:
                self.log_file.close()
            ts = QDateTime.currentDateTime().toString("yyyyMMdd_hhmmss")
            self.csv_file_path = os.path.join(self.csv_dir, f"Scans_{ts}_mini.csv")
            self.log_file_path = os.path.join(self.log_dir, f"log_{ts}.txt")
            try:
                self.csv_file = open(self.csv_file_path, "w", encoding="utf-8", newline="")
                self.log_file = open(self.log_file_path, "w", encoding="utf-8")
            except Exception as e:
                self.statusBar().showMessage(f"Cannot open files: {e}")
                return
            # Remove unwanted columns from headers
            headers = [
                "Timestamp", "MotorAngle_deg", "FilterPos",
                "Roll_deg", "Pitch_deg", "Yaw_deg", "AccelX_g", "AccelY_g", "AccelZ_g",
                "MagX_uT", "MagY_uT", "MagZ_uT",
                "Pressure_hPa", "Temperature_C", "TempCtrl_curr", "TempCtrl_set", "TempCtrl_aux",
                "Latitude_deg", "Longitude_deg", "IntegrationTime_us",
                "THP_Temp_C", "THP_Humidity_pct", "THP_Pressure_hPa"
            ]
            headers += [f"Pixel_{i}" for i in range(len(self.spec_ctrl.intens))]
            self.csv_file.write(",".join(headers) + "\n")
            self.csv_file.flush()
            os.fsync(self.csv_file.fileno())
            
            # Initialize data collection for averaging
            self._data_collection = []
            self._collection_start_time = QDateTime.currentDateTime()
            
            # Set timer interval based on integration time
            integration_time_ms = self.spec_ctrl.current_integration_time_us
            
            # For data collection, use a faster timer to collect samples
            # We'll collect samples at 250ms intervals
            self.collection_timer = QTimer(self)
            self.collection_timer.timeout.connect(self.collect_data_sample)
            self.collection_timer.start(250)  # Collect samples every 250ms
            
            # Set the save timer to match the integration time
            # This timer will trigger the averaging and saving of collected samples
            timer_interval = max(1000, min(5000, int(integration_time_ms)))
            self.save_data_timer.start(timer_interval)
            
            # Initialize hardware state tracking
            current_motor_angle = 0
            if hasattr(self.motor_ctrl, "current_angle_deg"):
                current_motor_angle = self.motor_ctrl.current_angle_deg
            
            current_filter_pos = self.filter_ctrl.get_position()
            if current_filter_pos is None:
                current_filter_pos = getattr(self.filter_ctrl, "current_position", 0)
            
            self._last_motor_angle = current_motor_angle
            self._last_filter_position = current_filter_pos
            self._hardware_changing = False
            
            self.continuous_saving = True
            self.spec_ctrl.toggle_btn.setText("Pause Saving")
            self.statusBar().showMessage(f"Saving started (interval: {timer_interval}ms)…")
            self.handle_status_message("Saving started")
        else:
            self.continuous_saving = False
            self.save_data_timer.stop()
            if hasattr(self, 'collection_timer'):
                self.collection_timer.stop()
            if self.csv_file:
                self.csv_file.close()
            if self.log_file:
                self.log_file.close()
            self.spec_ctrl.toggle_btn.setText("Start Saving")
            self.statusBar().showMessage("Saving stopped.")
            self.handle_status_message("Saving stopped")

    def collect_data_sample(self):
        """Collect a data sample for averaging, with pause on hardware state changes"""
        if not self.continuous_saving or not self.spec_ctrl.intens:
            return
        
        # Check for hardware state changes
        current_motor_angle = 0
        if hasattr(self.motor_ctrl, "current_angle_deg"):
            current_motor_angle = self.motor_ctrl.current_angle_deg
        
        current_filter_pos = self.filter_ctrl.get_position()
        if current_filter_pos is None:
            current_filter_pos = getattr(self.filter_ctrl, "current_position", 0)
        
        # If this is the first sample, initialize the tracking variables
        if not hasattr(self, '_last_motor_angle'):
            self._last_motor_angle = current_motor_angle
        if not hasattr(self, '_last_filter_position'):
            self._last_filter_position = current_filter_pos
        
        # Check if motor angle or filter position has changed
        motor_changed = abs(current_motor_angle - self._last_motor_angle) > 0.5  # 0.5 degree threshold
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
        
        # Create a copy of the current intensity data
        intensities = self.spec_ctrl.intens.copy()
        
        # Store the sample with timestamp
        sample = {
            'timestamp': QDateTime.currentDateTime(),
            'intensities': intensities
        }
        
        # Add to collection
        self._data_collection.append(sample)

    def save_continuous_data(self):
        """Average collected samples and save to CSV"""
        if not (self.csv_file and self.log_file) or not self.continuous_saving:
            return
        
        # If hardware is changing, don't save data
        if hasattr(self, '_hardware_changing') and self._hardware_changing:
            return
        
        try:
            # Check if we have collected any samples
            if not hasattr(self, '_data_collection') or not self._data_collection:
                return
            
            # Get the current time for this save operation
            now = QDateTime.currentDateTime()
            ts_csv = now.toString("yyyy-MM-dd hh:mm:ss.zzz")
            ts_txt = now.toString("yyyy-MM-dd hh:mm:ss")
            
            # Average the intensity data from all collected samples
            num_samples = len(self._data_collection)
            if num_samples == 0:
                return
            
            # Get the length of intensity data
            sample_length = len(self._data_collection[0]['intensities'])
            
            # Initialize array for averaging
            avg_intensities = [0.0] * sample_length
            
            # Sum all intensities
            for sample in self._data_collection:
                for i, val in enumerate(sample['intensities']):
                    if i < sample_length:
                        avg_intensities[i] += val
            
            # Divide by number of samples to get average
            avg_intensities = [val / num_samples for val in avg_intensities]
            
            # Get motor angle - ensure it's properly retrieved
            motor_angle = 0
            if hasattr(self.motor_ctrl, "current_angle_deg"):
                motor_angle = self.motor_ctrl.current_angle_deg
            
            # Get filter position
            filter_pos = self.filter_ctrl.get_position()
            if filter_pos is None:
                filter_pos = getattr(self.filter_ctrl, "current_position", 0)
            
            # Get IMU data - use the latest data directly from the IMU controller
            # The IMUController stores data in self.latest dictionary
            r, p, y = self.imu_ctrl.latest['rpy']
            
            # Check if accel, mag data exists in the latest dictionary
            ax, ay, az = 0, 0, 0
            if 'accel' in self.imu_ctrl.latest:
                ax, ay, az = self.imu_ctrl.latest['accel']
            
            mx, my, mz = 0, 0, 0
            if 'mag' in self.imu_ctrl.latest:
                mx, my, mz = self.imu_ctrl.latest['mag']
            
            pres = self.imu_ctrl.latest['pressure']
            temp_env = self.imu_ctrl.latest['temperature']
            lat = self.imu_ctrl.latest['latitude']
            lon = self.imu_ctrl.latest['longitude']
            
            # Get temperature controller data
            tc_curr = self.temp_ctrl.current_temp
            tc_set = self.temp_ctrl.setpoint
            tc_aux = self.temp_ctrl.auxiliary_temp
            
            # Get integration time
            integ_us = self.spec_ctrl.current_integration_time_us
            
            # Get THP sensor data
            thp = self.thp_ctrl.get_latest()
            thp_temp = thp.get("temperature", 0)
            thp_hum = thp.get("humidity", 0)
            thp_pres = thp.get("pressure", 0)
            
            # Create CSV row
            row = [
                ts_csv, str(motor_angle), str(filter_pos),
                f"{r:.2f}", f"{p:.2f}", f"{y:.2f}", f"{ax:.2f}", f"{ay:.2f}", f"{az:.2f}",
                f"{mx:.2f}", f"{my:.2f}", f"{mz:.2f}",
                f"{pres:.2f}", f"{temp_env:.2f}", f"{tc_curr:.2f}", f"{tc_set:.2f}", f"{tc_aux:.2f}",
                f"{lat:.6f}", f"{lon:.6f}", str(integ_us), f"{thp_temp:.2f}",
                f"{thp_hum:.2f}", f"{thp_pres:.2f}"
            ]
            
            # Add averaged intensity values
            row.extend([f"{val:.4f}" for val in avg_intensities])
            line = ",".join(row) + "\n"
            
            # Use buffer to reduce disk I/O operations
            if not hasattr(self, '_csv_buffer'):
                self._csv_buffer = []
                self._csv_buffer_count = 0
                self._csv_buffer_max = 5  # Write to disk every 5 samples
            
            # Add to buffer
            self._csv_buffer.append(line)
            self._csv_buffer_count += 1
            
            # Only write to disk when buffer is full
            if self._csv_buffer_count >= self._csv_buffer_max:
                self.csv_file.write(''.join(self._csv_buffer))
                self.csv_file.flush()
                self._csv_buffer = []
                self._csv_buffer_count = 0
            
            # Log file can be written immediately as it's much smaller
            peak = max(avg_intensities) if avg_intensities else 0
            txt_line = f"{ts_txt} | Peak {peak:.1f} (avg of {num_samples} samples)\n"
            self.log_file.write(txt_line)
            self.log_file.flush()
            
            # Clear the data collection for the next interval
            self._data_collection = []
            
        except Exception as e:
            print("save_continuous_data error:", e)
            self.statusBar().showMessage(f"Save error: {e}")

    def _update_indicators(self):
        # Update groupbox titles with connection status (green if connected, red if not)
        for ctrl, title, ok_fn in [
            (self.motor_ctrl, "Motor", self.motor_ctrl.is_connected),
            (self.filter_ctrl, "Filter Wheel", self.filter_ctrl.is_connected),
            (self.imu_ctrl, "IMU", self.imu_ctrl.is_connected),
            (self.spec_ctrl, "Spectrometer", self.spec_ctrl.is_ready),
            (self.temp_ctrl, "Temperature", lambda: hasattr(self.temp_ctrl, 'tc')),
            (self.thp_ctrl, "THP Sensor", self.thp_ctrl.is_connected)
        ]:
            col = "#4caf50" if ok_fn() else "#f44336"  # Green if connected, red if not
            gb = ctrl.groupbox if hasattr(ctrl, 'groupbox') else ctrl.widget
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
        if not self.log_file:
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
            self.log_file.write(log_line)
            self.log_file.flush()
            os.fsync(self.log_file.fileno())
        except Exception as e:
            print(f"Log write error: {e}")

    def closeEvent(self, event):
        """Handle window close event"""
        # Release camera resources if initialized
        if hasattr(self, 'camera') and self.camera.isOpened():
            self.camera.release()
        
        # Call the parent class closeEvent
        super().closeEvent(event)

    def load_routine_file(self):
        """Load a custom routine code file for automated hardware control"""
        from PyQt5.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Routine File", "", "Text Files (*.txt);;All Files (*)"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'r') as f:
                self.routine_commands = f.readlines()
            
            # Remove comments and empty lines
            self.routine_commands = [line.strip() for line in self.routine_commands 
                                    if line.strip() and not line.strip().startswith('#')]
            
            if self.routine_commands:
                self.routine_status.setText(f"Loaded: {os.path.basename(file_path)}\n{len(self.routine_commands)} commands")
                self.run_routine_btn.setEnabled(True)
                # Reset preset dropdown to avoid confusion
                self.preset_combo.setCurrentIndex(0)
            else:
                self.routine_status.setText("No valid commands in file")
                self.run_routine_btn.setEnabled(False)
                
        except Exception as e:
            self.statusBar().showMessage(f"Error loading routine: {e}")
            self.routine_status.setText(f"Error: {str(e)}")
            self.run_routine_btn.setEnabled(False)

    def run_routine(self):
        """Execute the loaded routine code commands"""
        if not hasattr(self, 'routine_commands') or not self.routine_commands:
            self.statusBar().showMessage("No routine loaded")
            return
        
        self.statusBar().showMessage("Starting routine execution...")
        self.routine_status.setText("Running routine...")
        self.run_routine_btn.setEnabled(False)
        
        # Create a timer to execute commands sequentially
        self.routine_index = 0
        self.routine_timer = QTimer(self)
        self.routine_timer.timeout.connect(self.execute_next_routine_command)
        self.routine_timer.start(1000)  # Start with 1 second interval

    def execute_next_routine_command(self):
        """Execute the next command in the schedule sequence"""
        if self.routine_index >= len(self.routine_commands):
            # All commands completed
            self.routine_timer.stop()
            self.routine_status.setText("Schedule execution completed")
            self.run_routine_btn.setEnabled(True)
            self.statusBar().showMessage("Schedule execution completed")
            return
        
        # Get the current command
        command = self.routine_commands[self.routine_index]
        self.routine_index += 1
        
        # Update status
        self.routine_status.setText(f"Running: {command}\nCommand {self.routine_index} of {len(self.routine_commands)}")
        
        try:
            # Parse and execute the command
            parts = command.split()
            if not parts:
                pass  # Empty command
            elif parts[0].lower() == "motor":
                # Example: motor move 1000
                if len(parts) >= 3 and parts[1].lower() == "move":
                    self.motor_ctrl.move_to(int(parts[2]))
            elif parts[0].lower() == "filter":
                # Example: filter position 3
                if len(parts) >= 3 and parts[1].lower() == "position":
                    self.filter_ctrl.set_position(int(parts[2]))
            elif parts[0].lower() == "spectrometer":
                # Example: spectrometer start
                if len(parts) >= 2:
                    if parts[1].lower() == "start":
                        self.spec_ctrl.start()
                    elif parts[1].lower() == "stop":
                        self.spec_ctrl.stop()
                    elif parts[1].lower() == "save":
                        self.spec_ctrl.save()
            elif parts[0].lower() == "wait":
                # Example: wait 5000 (wait for 5 seconds)
                if len(parts) >= 2:
                    try:
                        wait_ms = int(parts[1])
                        # Adjust timer interval for this wait
                        self.routine_timer.setInterval(wait_ms)
                        # Return without scheduling next command
                        return
                    except ValueError:
                        self.statusBar().showMessage(f"Invalid wait time: {parts[1]}")
            elif parts[0].lower() == "log":
                # Example: log This is a message
                if len(parts) >= 2:
                    message = " ".join(parts[1:])
                    self.statusBar().showMessage(message)
                    # Also log to file if logging is enabled
                    if hasattr(self, 'log_file') and self.log_file:
                        timestamp = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
                        self.log_file.write(f"{timestamp} - {message}\n")
                        self.log_file.flush()
            elif parts[0].lower() == "temp":
                # Example: temp setpoint 25.5
                if len(parts) >= 3 and parts[1].lower() == "setpoint":
                    try:
                        setpoint = float(parts[2])
                        if hasattr(self, 'temp_ctrl'):
                            self.temp_ctrl.set_setpoint(setpoint)
                    except ValueError:
                        self.statusBar().showMessage(f"Invalid temperature: {parts[2]}")
            else:
                self.statusBar().showMessage(f"Unknown command: {command}")
        
        except Exception as e:
            self.statusBar().showMessage(f"Error executing command: {e}")
        
        # Reset timer interval to default for next command
        self.routine_timer.setInterval(100)

    def update_camera_feed(self):
        """Update the camera feed display with optimized performance and error handling"""
        if not hasattr(self, '_updating'):
            self._updating = False
        
        if self._updating or not hasattr(self, 'camera'):
            return
        
        # Check if camera is opened
        try:
            camera_open = self.camera.isOpened()
        except Exception:
            camera_open = False
        
        if not camera_open:
            return
        
        self._updating = True
        try:
            ret, frame = self.camera.read()
            if ret:
                # Resize frame to reduce processing time (scale down by 50%)
                frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
                
                # Convert frame to RGB format for Qt
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = frame.shape
                bytes_per_line = ch * w
                
                # Convert to QImage and then to QPixmap
                qt_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(qt_image)
                
                # Scale pixmap to fit the label while maintaining aspect ratio
                self.cam_label.setPixmap(pixmap.scaled(
                    self.cam_label.width(), self.cam_label.height(),
                    Qt.KeepAspectRatio, Qt.FastTransformation
                ))
            else:
                # Don't show message every time to avoid flooding status bar
                if not hasattr(self, '_camera_error_count'):
                    self._camera_error_count = 0
                
                self._camera_error_count += 1
                if self._camera_error_count % 50 == 0:  # Show message every ~5 seconds
                    self.statusBar().showMessage("Warning: Could not read camera frame")
        except Exception as e:
            # Only show occasional error messages
            if not hasattr(self, '_camera_error_count'):
                self._camera_error_count = 0
            
            self._camera_error_count += 1
            if self._camera_error_count % 50 == 0:
                self.statusBar().showMessage(f"Camera error: {e}")
        finally:
            self._updating = False

    def closeEvent(self, event):
        """Handle window close event"""
        # Release camera resources if initialized
        if hasattr(self, 'camera') and self.camera.isOpened():
            self.camera.release()
        
        # Call the parent class closeEvent
        super().closeEvent(event)

    def load_routine_file(self):
        """Load a routine file for automated hardware control"""
        from PyQt5.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Routine File", "", "Text Files (*.txt);;All Files (*)"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'r') as f:
                self.routine_commands = f.readlines()
            
            # Remove comments and empty lines
            self.routine_commands = [line.strip() for line in self.routine_commands 
                                    if line.strip() and not line.strip().startswith('#')]
            
            if self.routine_commands:
                self.routine_status.setText(f"Loaded: {os.path.basename(file_path)}\n{len(self.routine_commands)} commands")
                self.run_routine_btn.setEnabled(True)
            else:
                self.routine_status.setText("No valid commands in file")
                self.run_routine_btn.setEnabled(False)
                
        except Exception as e:
            self.statusBar().showMessage(f"Error loading routine: {e}")
            self.routine_status.setText(f"Error: {str(e)}")
            self.run_routine_btn.setEnabled(False)

    def run_routine(self):
        """Execute the loaded routine commands"""
        if not hasattr(self, 'routine_commands') or not self.routine_commands:
            self.statusBar().showMessage("No routine loaded")
            return
        
        self.statusBar().showMessage("Starting routine execution...")
        self.routine_status.setText("Running routine...")
        self.run_routine_btn.setEnabled(False)
        
        # Create a timer to execute commands sequentially
        self.routine_index = 0
        self.routine_timer = QTimer(self)
        self.routine_timer.timeout.connect(self.execute_next_routine_command)
        self.routine_timer.start(1000)  # Start with 1 second interval

    def execute_next_routine_command(self):
        """Execute the next command in the routine"""
        if self.routine_index >= len(self.routine_commands):
            self.routine_timer.stop()
            self.routine_status.setText("Routine completed")
            self.run_routine_btn.setEnabled(True)
            self.statusBar().showMessage("Routine execution completed")
            return
        
        command = self.routine_commands[self.routine_index]
        self.routine_status.setText(f"Running: {command}")
        
        try:
            # Parse and execute the command
            parts = command.split()
            if not parts:
                pass  # Empty command
            elif parts[0].lower() == "motor":
                # Example: motor move 1000
                if len(parts) >= 3 and parts[1].lower() == "move":
                    self.motor_ctrl.move_to(int(parts[2]))
            elif parts[0].lower() == "filter":
                # Example: filter position 3
                if len(parts) >= 3 and parts[1].lower() == "position":
                    self.filter_ctrl.set_position(int(parts[2]))
            elif parts[0].lower() == "spectrometer":
                # Example: spectrometer start
                if len(parts) >= 2:
                    if parts[1].lower() == "start":
                        self.spec_ctrl.start()
                    elif parts[1].lower() == "stop":
                        self.spec_ctrl.stop()
                    elif parts[1].lower() == "save":
                        self.spec_ctrl.save()
            elif parts[0].lower() == "wait":
                # Example: wait 5000 (wait for 5 seconds)
                if len(parts) >= 2:
                    # Adjust timer interval for this step
                    wait_ms = int(parts[1])
                    self.routine_timer.setInterval(wait_ms)
            elif parts[0].lower() == "log":
                # Example: log This is a message
                message = " ".join(parts[1:])
                self.handle_status_message(message)
        
            self.routine_index += 1
        
        except Exception as e:
            self.statusBar().showMessage(f"Error in routine: {e}")
            self.routine_status.setText(f"Error: {str(e)}")
            self.routine_timer.stop()
            self.run_routine_btn.setEnabled(True)

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
        if hasattr(self, 'update_camera_feed'):
            self.update_camera_feed()

    # Add method to resume data collection after hardware change
    def _resume_after_hardware_change(self):
        """Resume data collection after hardware state change pause"""
        self._hardware_changing = False
        self.statusBar().showMessage("Resuming data collection after hardware change")
        self.handle_status_message("Resuming data collection")
        
        # Clear any existing data samples to ensure we only get fresh data
        if hasattr(self, '_data_collection'):
            self._data_collection = []

    # Add helper methods to MainWindow to access IMU data safely
    def get_imu_data(self):
        """Get IMU data with error handling"""
        try:
            if hasattr(self.imu_ctrl, 'latest'):
                return {
                    'rpy': self.imu_ctrl.latest.get('rpy', (0, 0, 0)),
                    'accel': self.imu_ctrl.latest.get('accel', (0, 0, 0)),
                    'mag': self.imu_ctrl.latest.get('mag', (0, 0, 0)),
                    'pressure': self.imu_ctrl.latest.get('pressure', 0),
                    'temperature': self.imu_ctrl.latest.get('temperature', 0),
                    'latitude': self.imu_ctrl.latest.get('latitude', 0),
                    'longitude': self.imu_ctrl.latest.get('longitude', 0)
                }
            return {
                'rpy': (0, 0, 0),
                'accel': (0, 0, 0),
                'mag': (0, 0, 0),
                'pressure': 0,
                'temperature': 0,
                'latitude': 0,
                'longitude': 0
            }
        except Exception as e:
            print(f"Error getting IMU data: {e}")
            return {
                'rpy': (0, 0, 0),
                'accel': (0, 0, 0),
                'mag': (0, 0, 0),
                'pressure': 0,
                'temperature': 0,
                'latitude': 0,
                'longitude': 0
            }

    def load_preset_schedule(self, index):
        """Load a preset schedule based on dropdown selection"""
        if index == 0:  # "Select Preset"
            return
        
        preset_name = self.preset_combo.currentText()
        
        # Define the paths for preset schedule files
        schedules_dir = os.path.join(os.path.dirname(__file__), "..", "schedules")
        os.makedirs(schedules_dir, exist_ok=True)
        
        preset_files = {
            "SO": os.path.join(schedules_dir, "schedule_so.txt"),
            "FU": os.path.join(schedules_dir, "schedule_fu.txt"),
            "RE": os.path.join(schedules_dir, "schedule_re.txt"),
            "SG": os.path.join(schedules_dir, "schedule_sg.txt")
        }
        
        file_path = preset_files.get(preset_name)
        
        if not file_path or not os.path.exists(file_path):
            # Create the preset file if it doesn't exist
            self._create_preset_schedule_file(preset_name, file_path)
        
        try:
            with open(file_path, 'r') as f:
                self.routine_commands = f.readlines()
            
            # Remove comments and empty lines
            self.routine_commands = [line.strip() for line in self.routine_commands 
                                    if line.strip() and not line.strip().startswith('#')]
            
            if self.routine_commands:
                self.routine_status.setText(f"Loaded: {preset_name} Schedule\n{len(self.routine_commands)} commands")
                self.run_routine_btn.setEnabled(True)
            else:
                self.routine_status.setText("No valid commands in preset file")
                self.run_routine_btn.setEnabled(False)
                
        except Exception as e:
            self.statusBar().showMessage(f"Error loading preset schedule: {e}")
            self.routine_status.setText(f"Error: {str(e)}")
            self.run_routine_btn.setEnabled(False)

    def _create_preset_schedule_file(self, preset_name, file_path):
        """Create a preset schedule file with default commands"""
        try:
            with open(file_path, 'w') as f:
                f.write(f"# {preset_name} Schedule - Created {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                if preset_name == "SO":
                    # Solar Observation Schedule
                    f.write("# Solar Observation Schedule\n")
                    f.write("log Starting Solar Observation Schedule\n")
                    f.write("motor move 0\n")
                    f.write("wait 2000\n")
                    f.write("filter position 1\n")
                    f.write("wait 1000\n")
                    f.write("spectrometer start\n")
                    f.write("wait 5000\n")
                    f.write("log Saving solar spectrum data\n")
                    f.write("spectrometer save\n")
                    f.write("wait 1000\n")
                    f.write("motor move 45\n")
                    f.write("wait 2000\n")
                    f.write("spectrometer save\n")
                    f.write("wait 1000\n")
                    f.write("log Solar Observation Schedule completed\n")
                
                elif preset_name == "FU":
                    # Full Spectrum Schedule
                    f.write("# Full Spectrum Schedule\n")
                    f.write("log Starting Full Spectrum Schedule\n")
                    f.write("motor move 90\n")
                    f.write("wait 2000\n")
                    f.write("filter position 2\n")
                    f.write("wait 1000\n")
                    f.write("spectrometer start\n")
                    f.write("wait 3000\n")
                    f.write("log Saving full spectrum data\n")
                    f.write("spectrometer save\n")
                    f.write("wait 1000\n")
                    f.write("filter position 3\n")
                    f.write("wait 1000\n")
                    f.write("spectrometer save\n")
                    f.write("wait 1000\n")
                    f.write("log Full Spectrum Schedule completed\n")
                
                elif preset_name == "RE":
                    # Reference Measurement Schedule
                    f.write("# Reference Measurement Schedule\n")
                    f.write("log Starting Reference Measurement Schedule\n")
                    f.write("motor move 180\n")
                    f.write("wait 2000\n")
                    f.write("filter position 1\n")
                    f.write("wait 1000\n")
                    f.write("spectrometer start\n")
                    f.write("wait 2000\n")
                    f.write("log Saving reference data\n")
                    f.write("spectrometer save\n")
                    f.write("wait 1000\n")
                    f.write("log Reference Measurement Schedule completed\n")
            
            self.statusBar().showMessage(f"Created preset schedule file: {preset_name}")
        
        except Exception as e:
            self.statusBar().showMessage(f"Error creating preset schedule file: {e}")












