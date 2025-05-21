from PyQt5.QtCore import QObject, pyqtSignal, QTimer, QDateTime
from PyQt5.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QPushButton, QTabWidget, 
    QWidget, QVBoxLayout as QVBoxLayout2, QLabel, QSpinBox, QCheckBox
)
import pyqtgraph as pg
from pyqtgraph import ViewBox
import numpy as np
import os

from drivers.spectrometer import (
    connect_spectrometer, AVS_MeasureCallback, AVS_MeasureCallbackFunc, 
    AVS_GetScopeData, StopMeasureThread, prepare_measurement, SpectrometerDriver
)

class SpectrometerController(QObject):
    status_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        # Group box UI
        self.groupbox = QGroupBox("Spectrometer")
        self.groupbox.setObjectName("spectrometerGroup")
        main_layout = QVBoxLayout()
        
        # Control buttons with larger font and bold text
        btn_layout = QHBoxLayout()
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.setStyleSheet("font-weight: bold; font-size: 11pt;")
        self.connect_btn.clicked.connect(self.connect)
        btn_layout.addWidget(self.connect_btn)
        
        self.start_btn = QPushButton("Start")
        self.start_btn.setStyleSheet("font-weight: bold; font-size: 11pt;")
        self.start_btn.setEnabled(False)
        self.start_btn.clicked.connect(self.start)
        btn_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setStyleSheet("font-weight: bold; font-size: 11pt;")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop)
        btn_layout.addWidget(self.stop_btn)
        
        self.save_btn = QPushButton("Save")
        self.save_btn.setStyleSheet("font-weight: bold; font-size: 11pt;")
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(self.save)
        btn_layout.addWidget(self.save_btn)
        
        self.toggle_btn = QPushButton("Start Saving")
        self.toggle_btn.setStyleSheet("font-weight: bold; font-size: 11pt;")
        self.toggle_btn.setEnabled(False)
        self.toggle_btn.clicked.connect(self.toggle)
        btn_layout.addWidget(self.toggle_btn)
        
        main_layout.addLayout(btn_layout)
        
        # Integration time controls with bold labels
        integ_layout = QHBoxLayout()

        integ_label = QLabel("Integration Time (ms):")
        integ_label.setStyleSheet("font-weight: bold;")
        integ_layout.addWidget(integ_label)

        self.integ_spinbox = QSpinBox()
        self.integ_spinbox.setRange(1, 4000)  # 1ms to 4s
        self.integ_spinbox.setValue(50)  # Default 50ms
        self.integ_spinbox.setSingleStep(10)
        integ_layout.addWidget(self.integ_spinbox)

        # Add the Apply Settings button
        self.apply_btn = QPushButton("Apply Settings")
        self.apply_btn.setEnabled(False)
        self.apply_btn.clicked.connect(self.update_measurement_settings)
        integ_layout.addWidget(self.apply_btn)

        # Removed auto-adjust checkbox

        main_layout.addLayout(integ_layout)

        # Cycles and repetitions controls with bold labels
        cycles_layout = QHBoxLayout()

        cycles_label = QLabel("Cycles:")
        cycles_label.setStyleSheet("font-weight: bold;")
        cycles_layout.addWidget(cycles_label)

        self.cycles_spinbox = QSpinBox()
        self.cycles_spinbox.setRange(1, 100)  # 1 to 100 cycles
        self.cycles_spinbox.setValue(1)  # Default 1 cycle
        self.cycles_spinbox.setSingleStep(1)
        cycles_layout.addWidget(self.cycles_spinbox)

        repetitions_label = QLabel("Repetitions:")
        repetitions_label.setStyleSheet("font-weight: bold;")
        cycles_layout.addWidget(repetitions_label)

        self.repetitions_spinbox = QSpinBox()
        self.repetitions_spinbox.setRange(1, 100)  # 1 to 100 repetitions
        self.repetitions_spinbox.setValue(1)  # Default 1 repetition
        self.repetitions_spinbox.setSingleStep(1)
        cycles_layout.addWidget(self.repetitions_spinbox)

        main_layout.addLayout(cycles_layout)

        # Spectral plots in tabs
        pg.setConfigOption('background', '#252525')
        pg.setConfigOption('foreground', '#e0e0e0')
        self.tab_widget = QTabWidget()

        # Tab 1: Wavelength vs Intensity
        tab1 = QWidget()
        layout1 = QVBoxLayout2(tab1)
        self.plot_wl = pg.PlotWidget()
        self.plot_wl.setLabel('bottom', 'Wavelength', 'nm')
        self.plot_wl.setLabel('left', 'Intensity', 'counts')
        self.plot_wl.showGrid(x=True, y=True, alpha=0.3)
        self.plot_wl.getViewBox().enableAutoRange(ViewBox.XYAxes, True)
        # Add a more attractive style
        self.curve_wl = self.plot_wl.plot([], [], pen=pg.mkPen('#4a86e8', width=2), 
                                         symbolBrush=(74, 134, 232), symbolPen='w', symbol='o', 
                                         symbolSize=5, name="Wavelength Spectrum")
        layout1.addWidget(self.plot_wl)
        self.tab_widget.addTab(tab1, "Wavelength vs Intensity")

        # Tab 2: Pixel vs Count
        tab2 = QWidget()
        layout2 = QVBoxLayout2(tab2)
        self.plot_px = pg.PlotWidget()
        # Set fixed range for x-axis (0-2048 pixels)
        self.plot_px.setXRange(0, 2048)
        self.plot_px.setLabel('bottom', 'Pixel', '')  # Remove 'Index' from label
        self.plot_px.setLabel('left', 'Count', '')
        # Enable auto-range only for y-axis
        self.plot_px.getViewBox().enableAutoRange(ViewBox.YAxis, True)
        self.plot_px.getViewBox().setAutoVisible(y=True)
        self.plot_px.showGrid(x=True, y=True, alpha=0.3)

        # Configure x-axis ticks to show 0, 100, 200, etc.
        x_axis = self.plot_px.getAxis('bottom')
        x_ticks = [(i, str(i)) for i in range(0, 2049, 100)]  # Create ticks at 0, 100, 200, etc.
        x_axis.setTicks([x_ticks])

        # Add a more attractive style
        self.curve_px = self.plot_px.plot([], [], pen=pg.mkPen('#f44336', width=2),
                                         fillLevel=0, fillBrush=pg.mkBrush(244, 67, 54, 50),
                                         name="Pixel Counts")
        layout2.addWidget(self.plot_px)
        self.tab_widget.addTab(tab2, "Pixel vs Count")
        # Add the tab widget to the groupbox layout
        main_layout.addWidget(self.tab_widget)
        self.groupbox.setLayout(main_layout)

        # Internal state
        self._ready = False
        self.handle = None
        self.wls = []
        self.intens = []
        self.npix = 0

        # Ensure parent MainWindow's toggle_data_saving is used if parent exists
        if parent is not None:
            try:
                self.toggle_btn.clicked.disconnect(self.toggle)
            except Exception:
                pass
            self.toggle_btn.clicked.connect(parent.toggle_data_saving)

        # Data directory for snapshots
        self.csv_dir = "data"
        os.makedirs(self.csv_dir, exist_ok=True)

        # Timer for updating plot
        self.plot_timer = QTimer(self)
        self.plot_timer.timeout.connect(self._update_plot)
        self.plot_timer.start(200)  # update plot at 5 Hz

        # Add downsampling for plots
        self.downsample_factor = 2  # Only plot every 2nd point

        # Add new attributes
        self.driver = SpectrometerDriver()
        self.active_spectrometers = {}  # Track multiple spectrometers
        self.watchdog_timer = QTimer()
        self.watchdog_timer.timeout.connect(self._check_measurement_status)
        self.watchdog_timer.start(1000)  # Check every second

    def connect(self):
        # Emit status for feedback
        self.status_signal.emit("Connecting to spectrometer...")
        try:
            handle, wavelengths, num_pixels, serial_str = connect_spectrometer()
        except Exception as e:
            self.status_signal.emit(f"Connection failed: {e}")
            return
        self.handle = handle
        # Store wavelength calibration and number of pixels
        self.wls = wavelengths.tolist() if isinstance(wavelengths, np.ndarray) else wavelengths
        self.npix = num_pixels
        self._ready = True
        # Enable measurement start once connected
        self.start_btn.setEnabled(True)
        self.status_signal.emit(f"Spectrometer ready (SN={serial_str})")

    def start(self):
        if not self._ready:
            self.status_signal.emit("Spectrometer not ready")
            return
        
        # Get integration time from UI
        integration_time = float(self.integ_spinbox.value())
        
        # Get cycles and repetitions from UI
        cycles = self.cycles_spinbox.value()
        repetitions = self.repetitions_spinbox.value()
        
        # Calculate averages based on integration time
        # For shorter integration times, use more averages to improve signal quality
        # For longer integration times, use fewer averages to maintain responsiveness
        if integration_time < 10:
            averages = 10  # More averages for very short integration times
        elif integration_time < 100:
            averages = 5   # Medium averages for short integration times
        elif integration_time < 1000:
            averages = 2   # Few averages for medium integration times
        else:
            averages = 1   # No averaging for long integration times
        
        # Store current integration time for data saving
        self.current_integration_time_us = integration_time
        
        # Update status with current settings
        self.status_signal.emit(f"Starting measurement (Int: {integration_time}ms, Avg: {averages}, Cycles: {cycles}, Rep: {repetitions})")
        
        code = prepare_measurement(self.handle, self.npix, 
                                  integration_time_ms=integration_time, 
                                  averages=averages,
                                  cycles=cycles,
                                  repetitions=repetitions)
        if code != 0:
            self.status_signal.emit(f"Prepare error: {code}")
            return
        self.measure_active = True
        self.cb = AVS_MeasureCallbackFunc(self._cb)
        err = AVS_MeasureCallback(self.handle, self.cb, -1)
        if err != 0:
            self.status_signal.emit(f"Callback error: {err}")
            self.measure_active = False
            return
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.apply_btn.setEnabled(True)  # Enable the apply button when measurement starts
        self.status_signal.emit("Measurement started")

    def _cb(self, p_data, p_user):
        # Spectrometer driver callback (on new scan)
        status_code = p_user[0]
        if status_code == 0:
            _, data = AVS_GetScopeData(self.handle)
            # Ensure intensities list has correct length (up to 2048)
            max_pixels = min(2048, self.npix)
            full = [0.0] * max_pixels
            # Copy only the data we need (up to 2048 pixels)
            data_to_use = data[:max_pixels] if len(data) > max_pixels else data
            full[:len(data_to_use)] = data_to_use
            self.intens = full
            
            # Make sure integration time is accessible to MainWindow
            if hasattr(self, 'current_integration_time_us'):
                # Make it accessible to parent (MainWindow)
                if hasattr(self, 'parent') and self.parent is not None:
                    if not callable(self.parent):  # Check if parent is not a method
                        self.parent.current_integration_time_us = self.current_integration_time_us
            
            # Enable snapshot save and continuous save after first data received
            self.save_btn.setEnabled(True)
            self.toggle_btn.setEnabled(True)
        else:
            self.status_signal.emit(f"Spectrometer error code {status_code}")

    def _update_plot(self):
        """Update the plots with intensity data, ensuring arrays have matching shapes"""
        if not self.intens:
            return
        
        try:
            # Get the data arrays
            intensities = np.array(self.intens)
            wavelengths = np.array(self.wls) if self.wls else np.arange(len(intensities))
            
            # Ensure arrays are the same length
            min_length = min(len(intensities), len(wavelengths))
            intensities = intensities[:min_length]
            wavelengths = wavelengths[:min_length]
            
            # Create pixel indices array
            pixel_indices = np.arange(len(intensities))
            
            # Apply downsampling to reduce points plotted
            if hasattr(self, 'downsample_factor') and self.downsample_factor > 1:
                step = self.downsample_factor
                # Use numpy indexing for consistent slicing
                mask = np.zeros(len(intensities), dtype=bool)
                mask[::step] = True
                
                # Apply mask to all arrays
                intensities = intensities[mask]
                wavelengths = wavelengths[mask]
                pixel_indices = pixel_indices[mask]
            
            # Update wavelength plot
            self.curve_wl.setData(wavelengths, intensities)
            
            # Update pixel plot
            self.curve_px.setData(pixel_indices, intensities)
            
            # Auto-adjust y-axis range based on current data, but not too frequently
            if not hasattr(self, '_range_update_counter'):
                self._range_update_counter = 0
            
            self._range_update_counter += 1
            if self._range_update_counter >= 5:  # Only update range every 5 cycles
                self._range_update_counter = 0
                if len(intensities) > 0 and np.max(intensities) > 0:
                    # Add 10% padding to the top of the y-range
                    max_y = np.max(intensities) * 1.1
                    self.plot_px.setYRange(0, max_y)
            
            # Removed auto-adjust integration time functionality
        
        except Exception as e:
            # Log the error but don't crash
            print(f"Plot update error: {e}")
            # Try to recover by clearing the plots
            try:
                self.curve_wl.setData([], [])
                self.curve_px.setData([], [])
            except:
                pass

    def stop(self):
        if not hasattr(self, 'measure_active') or not self.measure_active:
            return
        self.measure_active = False
        th = StopMeasureThread(self.handle, parent=self)
        th.finished_signal.connect(self._on_stop)
        th.start()

    def _on_stop(self):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.apply_btn.setEnabled(False)  # Disable the apply button when measurement stops
        self.status_signal.emit("Measurement stopped")

    def save(self):
        ts = QDateTime.currentDateTime().toString("yyyyMMdd_hhmmss")
        path = os.path.join(self.csv_dir, f"snapshot_{ts}.csv")
        try:
            with open(path, 'w') as f:
                f.write("Wavelength (nm),Intensity\n")
                for wl, inten in zip(self.wls, self.intens):
                    if inten != 0:
                        f.write(f"{wl:.4f},{inten:.4f}\n")
            self.status_signal.emit(f"Saved snapshot to {path}")
        except Exception as e:
            self.status_signal.emit(f"Save error: {e}")

    def toggle(self):
        # This method is overridden by MainWindow if parent is provided.
        self.status_signal.emit("Continuous-save not yet implemented")

    def is_ready(self):
        return self._ready

    def update_measurement_settings(self):
        """Update measurement settings without stopping the current measurement"""
        if not self._ready:
            self.status_signal.emit("Spectrometer not ready")
            return
        
        # Get all settings from UI
        integration_time = float(self.integ_spinbox.value())
        cycles = self.cycles_spinbox.value()
        repetitions = self.repetitions_spinbox.value()
        
        # Calculate averages based on integration time
        if integration_time < 10:
            averages = 10
        elif integration_time < 100:
            averages = 5
        elif integration_time < 1000:
            averages = 2
        else:
            averages = 1
        
        # Store current integration time for data saving
        self.current_integration_time_us = integration_time 
        
        if hasattr(self, 'measure_active') and self.measure_active:
            # First stop the current measurement
            self.status_signal.emit(f"Stopping measurement to update settings...")
            self.measure_active = False
            
            # Use StopMeasureThread to properly stop the measurement
            th = StopMeasureThread(self.handle, parent=self)
            th.finished_signal.connect(lambda: self._apply_new_settings(integration_time, averages, cycles, repetitions))
            th.start()
        else:
            # Just prepare the measurement with new settings
            code = prepare_measurement(self.handle, self.npix, 
                                      integration_time_ms=integration_time, 
                                      averages=averages,
                                      cycles=cycles,
                                      repetitions=repetitions)
            if code != 0:
                self.status_signal.emit(f"Settings update error: {code}")
                return
            self.status_signal.emit(f"Settings updated (Int: {integration_time}ms, Avg: {averages}, Cycles: {cycles}, Rep: {repetitions})")

    def _apply_new_settings(self, integration_time, averages, cycles, repetitions):
        """Helper to apply new settings after measurement has stopped"""
        code = prepare_measurement(self.handle, self.npix, 
                                  integration_time_ms=integration_time, 
                                  averages=averages,
                                  cycles=cycles,
                                  repetitions=repetitions)
        if code != 0:
            self.status_signal.emit(f"Settings update error: {code}")
            return
        
        self.cb = AVS_MeasureCallbackFunc(self._cb)
        err = AVS_MeasureCallback(self.handle, self.cb, -1)
        if err != 0:
            self.status_signal.emit(f"Callback error on restart: {err}")
            self.measure_active = False
            return
        
        self.measure_active = True
        self.stop_btn.setEnabled(True)
        self.status_signal.emit(f"Settings updated (Int: {integration_time}ms, Avg: {averages}, Cycles: {cycles}, Rep: {repetitions})")

    # Removed auto_adjust_integration_time method
    # def auto_adjust_integration_time(self):
    #     """Automatically adjust integration time based on peak value and filter wheel position"""
    #     ...

    def connect_spectrometer(self, ispec=0):
        """Connect to a specific spectrometer by index"""
        success, message = self.driver.reset(ispec, ini=True)
        if success:
            self.active_spectrometers[ispec] = True
            self.status_signal.emit(message)
            # Update UI elements
            self.start_btn.setEnabled(True)
            return True
        else:
            self.status_signal.emit(message)
            return False

    def disconnect_spectrometer(self, ispec=0, free_resources=False):
        """Disconnect from a specific spectrometer"""
        success, message = self.driver.disconnect(ispec, dofree=free_resources)
        if success and ispec in self.active_spectrometers:
            del self.active_spectrometers[ispec]
        self.status_signal.emit(message)
        return success

    def set_integration_time(self, ispec=0, integration_time=50.0):
        """Set integration time for a specific spectrometer"""
        success, message = self.driver.set_it(ispec, integration_time)
        self.status_signal.emit(message)
        return success

    def start_measurement(self, ispec=0, cycles=1):
        """Start measurement on a specific spectrometer"""
        if ispec not in self.active_spectrometers:
            self.status_signal.emit(f"Spectrometer {ispec} not connected")
            return False
            
        # Get integration time from UI
        integration_time = float(self.integ_spinbox.value())
        
        # Set integration time
        self.set_integration_time(ispec, integration_time)
        
        # Start measurement
        success, message = self.driver.measure(ispec, ncy=cycles)
        self.status_signal.emit(message)
        
        if success:
            self.measure_active = True
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.apply_btn.setEnabled(True)
        
        return success

    def stop_measurement(self, ispec=0):
        """Stop measurement on a specific spectrometer"""
        if ispec not in self.active_spectrometers:
            return False
            
        if hasattr(self, 'measure_active') and self.measure_active:
            self.measure_active = False
            th = StopMeasureThread(self.driver.handles[ispec]['handle'], parent=self)
            th.finished_signal.connect(self._on_stop)
            th.start()
            return True
        return False

    def get_temperature(self, ispec=0, board_temp=False):
        """Get temperature from spectrometer"""
        success, message, temp = self.driver.get_temp(ispec, syst8i=board_temp)
        if success:
            self.status_signal.emit(f"Temperature: {temp:.1f}°C")
            return temp
        else:
            self.status_signal.emit(message)
            return None

    def _check_measurement_status(self):
        """Watchdog function to check measurement status"""
        for ispec in self.active_spectrometers:
            if ispec in self.driver.data_status:
                status = self.driver.data_status[ispec]
                
                if status == 'DATA_READY':
                    # Process new data
                    self._process_new_data(ispec)
                    
                elif status == 'ERROR':
                    # Handle error condition
                    error_level = self.driver.recovery_level.get(ispec, 0)
                    self.status_signal.emit(f"Spectrometer {ispec} error (level {error_level})")

    def _process_new_data(self, ispec):
        """Process new data from spectrometer"""
        if ispec in self.driver.handles and 'last_data' in self.driver.handles[ispec]:
            data = self.driver.handles[ispec]['last_data']
            wavelengths = self.driver.handles[ispec]['wavelengths']
            
            # Update the data for plotting
            self.intens = data
            
            # Check for saturation
            if self.driver.handles[ispec].get('saturated', False):
                self.status_signal.emit("Warning: Detector saturation detected")
                
            # Reset data status to prevent reprocessing
            self.driver.data_status[ispec] = 'PROCESSED'
            
            # Enable snapshot save and continuous save after data received
            self.save_btn.setEnabled(True)
            self.toggle_btn.setEnabled(True)


