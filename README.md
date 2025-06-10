# Mini ROBOHyPO User Manual

## 1. Introduction

### 1.1. About Mini ROBOHyPO (by SciGlob Instruments)

Welcome to the Mini ROBOHyPO software! This application is developed by SciGlob Instruments to control and manage the Mini ROBOHyPO system, a sophisticated instrument designed for [**Note to User Manual Author:** Briefly describe the primary domain/purpose of the Mini ROBOHyPO instrument itself, e.g., "hyperspectral remote sensing," "environmental monitoring," "material analysis," etc. This information is not in the provided code files but is crucial for context.].

### 1.2. Purpose of the Software

The Mini ROBOHyPO control software provides a comprehensive interface for:

*   Configuring and controlling various hardware components of the Mini ROBOHyPO system.
*   Visualizing data acquired from these components, primarily the spectrometer and camera.
*   Automating measurement sequences through routines.
*   Logging and saving acquired data for later analysis.

### 1.3. Key Capabilities Overview

This software enables you to:

*   **Control Hardware**: Manage the spectrometer, motorized rotation stage, filter wheel, temperature controller, IMU (Inertial Measurement Unit), and THP (Temperature, Humidity, Pressure) sensor.
*   **Visualize Data**: View live spectral plots, camera feeds, and sensor readings.
*   **Automate Measurements**: Create and run custom routines for automated data acquisition sequences.
*   **Log Data**: Continuously log data from all connected sensors and the spectrometer to CSV and text files.
*   **Configure System**: Set up hardware parameters, including COM ports.
*   **Error Reporting**: Receive feedback on system status and potential errors through on-screen messages and dialogs.

## 2. Getting Started

### 2.1. System Requirements

*   **Operating System**: Windows (tested on Windows 10/11), Linux, macOS.
*   **Python**: Python 3.9 or newer.
*   **Libraries**: The system relies on several Python libraries. These are typically listed in a `requirements.txt` file. Key libraries include:
    *   `PyQt5` (for the graphical user interface)
    *   `NumPy` (for numerical operations)
    *   `pyqtgraph` (for plotting)
    *   `pyserial` (for hardware communication)
    *   `opencv-python` (for camera access)
    *   `astral` (for sun position calculations, if used by specific features not detailed here)
    *   `pandas` (for data processing in routines, e.g., PO routine plot)
    *   `matplotlib` (for routine result plots)
    *   `libscrc` (optional, for faster Modbus CRC calculation if applicable to your hardware)
    *   The Avantes spectrometer SDK (e.g., `avaspec.dll` or platform equivalent) must be installed and accessible by the software.

### 2.2. Installation (Running from source)

To run the Mini ROBOHyPO software from source:

1.  **Ensure Python is installed** on your system.
2.  **Obtain the Software**: Download or clone the Mini ROBOHyPO software source code to a local directory.
3.  **Install Required Libraries**: Open a terminal or command prompt, navigate to the software's root directory, and install the dependencies:
    ```bash
    pip install -r requirements.txt
    ```
    (Note: If a `requirements.txt` file is not provided or is incomplete, you may need to install the libraries listed in Section 2.1 manually using `pip install [library_name]`).
4.  **Avantes SDK**: Ensure the Avantes spectrometer SDK (DLL files such as `avaspec.dll` or `avaspecx64.dll` for Windows, or corresponding shared libraries for Linux/macOS) is present in the application's `drivers` sub-directory, or in a system directory where libraries are typically found (e.g., within the system's PATH on Windows).
5.  **Hardware Drivers**: Ensure any other necessary drivers for your specific hardware (e.g., USB-to-Serial adapters for COM port devices) are installed on your operating system.

### 2.3. Hardware Connections

Before launching the software, ensure all hardware components of the Mini ROBOHyPO system are correctly connected to your computer:

*   **Spectrometer**: Typically connected via USB.
*   **Motor, Filter Wheel, Temperature Controller, IMU, THP Sensor**: These usually connect via USB, often appearing as virtual COM ports on your system.
*   **Camera**: Connect your camera (e.g., a USB webcam if an external one is used, or ensure the default system camera is operational).

Refer to the Mini ROBOHyPO system hardware manual for detailed connection instructions and diagrams.

### 2.4. Launching the Application

1.  Navigate to the root directory of the software using a terminal or command prompt.
2.  Run the main application script:
    ```bash
    python main.py
    ```
3.  A splash screen (`asset/splash.jpg`) will appear briefly, followed by the main application window.

### 2.5. Understanding `hardware_config.json`

The `hardware_config.json` file, located in the application's root directory (or one level up from `gui/main_window.py`), allows you to pre-configure the COM (serial) ports for various hardware components. This avoids needing to manually select them in the UI each time, especially if your setup is consistent.

**Structure:**
The file is a JSON object with key-value pairs, where the key is the device name and the value is its assigned COM port string.

**Key Parameters:**

*   `"filterwheel"`: COM port for the Filter Wheel (e.g., `"COM12"` on Windows, or `/dev/ttyUSB0` on Linux).
*   `"imu"`: COM port for the IMU (e.g., `"COM14"`).
*   `"motor"`: COM port for the Motor (e.g., `"COM11"`).
*   `"temp_controller"`: COM port for the Temperature Controller (e.g., `"COM13"`).
*   `"thp_sensor"`: COM port for the THP Sensor (e.g., `"COM10"`).

**Example `hardware_config.json`:**
```json
{
  "filterwheel": "COM12",
  "imu": "COM14",
  "motor": "COM11",
  "temp_controller": "COM13",
  "thp_sensor": "COM10"
}
```
If a device fails to connect on the configured port (or if the file is missing/misconfigured), you can usually select a different port manually from its control panel within the software.

## 3. Main User Interface Overview

The Mini ROBOHyPO software features a single main window designed for comprehensive control and monitoring. The UI has a dark theme for comfortable viewing.

### 3.1. Main Window Layout

The main window is divided into two primary sections by a draggable horizontal splitter:

#### 3.1.1. Spectrometer Control & Plot Area (Left Panel)
This panel occupies the larger portion of the window and is dedicated to spectrometer operations. It includes:
*   Controls for connecting to the spectrometer.
*   Buttons to **Start**, **Stop** spectral measurements and **Save** individual scans.
*   A button to toggle continuous data logging (**Start Saving** / **Stop Saving**).
*   Input fields for setting **Integration Time (ms)**, **Cycles**, and **Repetitions**.
*   An **Apply Settings** button for measurement parameters.
*   A large plot area that displays the live spectrum (intensity vs. pixel number) and any static snapshot overlays captured during routines.

#### 3.1.2. Camera Feed Panel (Right Panel, Top)
Located at the top of the right-hand panel, this section displays:
*   A live video feed from the connected camera.
*   A placeholder message ("Camera feed will appear here") if the camera is not available or not initialized.

#### 3.1.3. Routine Control Panel (Right Panel, Middle)
This panel allows for the automation of measurement sequences:
*   **Preset Routines**: A dropdown list (`Preset:`) to select from predefined measurement sequences.
*   **Load File Button**: Opens a file dialog to load custom routines from `.txt` files.
*   **Run Code / Stop Button**: Starts or halts the execution of the loaded routine. (Label changes based on state).
*   **Status Display**: A label shows the name of the loaded routine and its current execution status (e.g., "No routine loaded", "Running command X/Y", "Routine completed").

#### 3.1.4. Hardware Control Panels (Right Panel, Bottom Grid)
Below the Routine Control panel, a grid layout hosts individual control panels for other connected hardware. Each panel is a `QGroupBox` with a title indicating the device.
*   **Temperature Controller Panel**
*   **Motor Controller Panel**
*   **Filter Wheel Controller Panel**
*   **IMU Panel**
*   **THP Sensor Panel**

Details for each panel are in Section 5. Each hardware panel includes a connection status indicator (see Section 5.1) and relevant controls.

### 3.2. Status Bar

The status bar is located at the very bottom of the main window. It provides real-time feedback on:
*   Application status (e.g., "Application initialized", "Data saving started").
*   Ongoing operations and their progress.
*   Connection status of hardware components (e.g., "Connected to filter wheel on COMXX").
*   Errors or warnings encountered by the system.
*   Log messages from running routines.

Pay attention to the status bar for important updates and system messages.

### 3.3. Exiting the Application

To exit the Mini ROBOHyPO software:
1.  Close the main window (e.g., by clicking the "X" button in the window's title bar).
2.  A confirmation dialog will appear: "Do you want to quit?".
    *   Click **Yes** to proceed with shutting down the application. The software will attempt to disconnect from all hardware and clean up resources. A warning dialog may appear if cleanup encounters significant issues.
    *   Click **No** to cancel and return to the application.

## 4. Core Features and Functionalities

This section details the primary features and how to use them.

### 4.1. Spectrometer Control

The **Spectrometer** panel on the left side of the main window is your primary interface for controlling the spectrometer.

#### 4.1.1. Connecting to the Spectrometer
- **Automatic Connection**: On startup, the software attempts to automatically connect to the spectrometer. This process may involve a short delay and retries if the first attempt fails.
- **Manual Connection**: Use the **Connect** button (which toggles to **Disconnect** when connected) in the Spectrometer panel.
- **Status Indicator**: See Section 5.1 for details on the colored dot (●) connection indicator.
- **Feedback**: Connection progress and status (e.g., "Spectrometer ready (SN=XXXX)") are shown in the main Status Bar.

#### 4.1.2. Setting Integration Time & Averaging
- **Integration Time (ms)**: Adjust the `Integration Time (ms)` spinbox to set the duration the spectrometer collects light for a single scan. Values typically range from 1 to 4000 ms.
- **Cycles**: Set the `Cycles` spinbox for the number of measurements to be internally averaged by the spectrometer hardware for certain measurement modes (1-100). This is a hardware averaging feature.
- **Repetitions**: Set the `Repetitions` spinbox for the number of measurements to be taken sequentially (1-100).
- **Software Averaging (Automatic)**: For short integration times, the software may automatically average multiple scans to improve the signal-to-noise ratio. This is not directly set by the user but is reported in status messages (e.g., "Avg: 5") when starting a measurement.
- **Apply Settings Button**: After changing Integration Time, Cycles, or Repetitions, click the **Apply Settings** button. If a measurement is active, it will be stopped and then restarted with the new settings.

#### 4.1.3. Starting and Stopping Measurements (Live View)
- **Start Button**: Click to begin live measurements. The spectral data will be displayed on the plot in real-time.
- **Stop Button**: Click to halt the current measurement.
- **UI Feedback**: The **Start** and **Stop** buttons enable/disable based on whether a measurement is active. The **Apply Settings** button is typically enabled only when a measurement is active.

#### 4.1.4. Saving Single Scans (Dark/White Reference, etc.)
- **Save Button**: After a measurement provides data (either a live scan or a scan initiated by a routine), click the **Save** button.
- **File Format**: This saves the currently displayed spectrum data as a CSV (Comma Separated Values) file.
- **Naming Convention**: Files are saved in the `data/` directory with a timestamped name, typically `snapshot_[timestamp].csv`.
- **Content**: The CSV file contains two columns: "Pixel" and "Intensity".
- **Use Cases**: This feature is useful for capturing reference spectra, such as dark spectra (with the light path blocked or light source off) or white references (using a calibrated reflectance standard), or any other single spectrum of interest.

#### 4.1.5. Continuous Data Saving
- **Toggle Button**: The **Start Saving** / **Stop Saving** button in the Spectrometer panel controls continuous data logging.
- **Functionality**: When active, data from all connected and reporting hardware (spectrometer, motor, filter wheel, IMU, THP, temperature controller), along with timestamps and current routine code (if any), are logged into a main CSV file.
- **File Location**: CSV files are saved in the `data/` directory, named `Scans_[timestamp]_mini.csv`.
- **Log File**: A corresponding text log file (`logs/log_[timestamp].txt`) is also created. This file contains status messages from the application and hardware, as well as a summary of each spectrometer reading taken during continuous saving (timestamp and peak intensity).
- **Data Rate**: The data collection interval is primarily based on the spectrometer's integration time. Data is buffered and written to the CSV file every 5 samples to optimize disk access.
- **Automatic Pausing**: Continuous data collection automatically pauses for 2 seconds if the motor or filter wheel moves, to avoid logging potentially unstable data during hardware transitions.

#### 4.1.6. Understanding Spectrometer Plots
- **Live Data**: The main plot displays the live spectrum from the spectrometer, showing intensity counts for each pixel of the detector.
- **X-Axis (Pixel)**: Represents the pixel number of the spectrometer's detector (typically 0 to 2047, or as per your spectrometer's specification). Major ticks are shown every 100 pixels.
- **Y-Axis (Count)**: Represents the intensity (raw counts) measured by each pixel. This axis auto-ranges to fit the incoming data, with some padding at the top for better visualization.
- **Grid**: A grid is displayed for easier reading of values.
- **Static Overlays**: When using the `plot` command in routines (see Section 4.3.6), snapshots of spectra can be added as static curves to this plot. These are displayed with different, randomly assigned colors. Up to 5 such static curves are kept on the plot; older ones are removed as new ones are added by the `plot` command.
- **Plot Title**: The plot title can change to reflect the current state, such as indicating a "Final Scan" from a routine or when static curves are added or cleared.

### 4.2. Camera Feed

#### 4.2.1. Viewing the Live Feed
- **Location**: The camera feed is displayed in the **Camera Feed** panel, located at the top of the right-hand section of the main window.
- **Source**: The software attempts to use the default system camera (usually camera index 0).
- **Display**: Shows a live video stream. If the camera cannot be opened or an error occurs, a placeholder message ("Camera feed will appear here") is shown, and a warning message appears in the main Status Bar.
- **Updates**: The feed typically updates at approximately 10 frames per second.
- **Resizing**: The video display automatically resizes to fit the allocated panel space while maintaining the camera's original aspect ratio.

### 4.3. Routine Management

Routines allow for automated sequences of operations, controlling various hardware components and data acquisition processes.

#### 4.3.1. Understanding Routines
- **Format**: Routines are defined as plain text files (typically with a `.txt` extension).
- **Commands**: Each line in the file represents a single command to be executed.
- **Comments**: Lines starting with a `#` symbol are treated as comments and are ignored by the parser.
- **Execution**: Commands are executed sequentially. The Routine Manager uses timers to handle `wait` commands and to sequence operations, ensuring the main user interface remains responsive.

#### 4.3.2. Loading Preset Routines
- **UI**: Use the **Preset:** dropdown menu in the **Routine Control** panel.
- **Selection**: Choose a routine from the list (e.g., "Standard Scan", "Dark Reference", "PO Routine").
- **Loading**: Selecting a preset automatically loads the corresponding routine file from the `routines/` sub-directory within the application's folder structure.
- **Default Routines**: The software may automatically create several default routines (e.g., `standard_scan.txt`, `dark_reference.txt`, `po_routine.txt`, `integration_test.txt`) in the `routines/` directory if they don't already exist. These provide examples and starting points for common tasks.

#### 4.3.3. Loading Custom Routine Files
- **UI**: Click the **Load File** button in the **Routine Control** panel.
- **File Dialog**: This opens a standard file dialog, allowing you to browse for routine files.
- **Default Directory**: The dialog typically opens to the `routines/` directory.
- **File Type**: Select your `.txt` routine file.

#### 4.3.4. Running and Stopping Routines
- **Run/Stop Button**:
    - If a routine is loaded and not currently running, the button will display **Run Code**. Clicking it starts the execution of the loaded routine from the first command.
    - If a routine is currently running, the button will display **Stop**. Clicking it will halt the routine execution immediately (or after the current step completes its non-interruptible phase).
- **Execution Flow**: The Routine Manager executes commands one by one. For commands that involve delays (e.g., `wait`) or hardware operations, the manager typically schedules the next command after the specified delay or an estimated time for the hardware action.

#### 4.3.5. Routine Status Display
- **UI**: A label within the **Routine Control** panel provides feedback on the routine's state.
- **Information Displayed**:
    - "No routine loaded"
    - "Loaded: [filename.txt]" (after a routine is successfully loaded)
    - "Running command [current_command_number]/[total_commands]: [current_command_text]"
    - "Routine completed"
    - "Routine stopped" (if manually stopped)
    - "Error loading routine" (if the file cannot be parsed)

#### 4.3.6. Available Routine Commands
The following commands can be used in `.txt` routine files. Command keywords are generally case-insensitive. Parameters in `<angle brackets>` are placeholders for values you provide.

-   `log <message>`
    *   **Description**: Displays the `<message>` in the main window's status bar and also prints it to the application's console output. Useful for tracking routine progress.
    *   **Example**: `log Starting measurement sequence`
-   `wait <time_ms>`
    *   **Description**: Pauses routine execution for the specified `<time_ms>` in milliseconds.
    *   **Example**: `wait 2000` (waits for 2 seconds)
-   `motor move <angle>`
    *   **Description**: Commands the Motor Controller to move the motor to the specified `<angle>` in degrees.
    *   **Example**: `motor move 90.5`
-   `filter position <position_number>`
    *   **Description**: Commands the Filter Wheel Controller to set the filter wheel to the specified `<position_number>` (typically an integer from 1 to 6).
    *   **Example**: `filter position 3`
-   `integration <time_ms>`
    *   **Description**: Sets the spectrometer's integration time to `<time_ms>` milliseconds. This updates the value in the Spectrometer UI panel and applies the setting to the main spectrometer (which may involve stopping and restarting an active measurement).
    *   **Example**: `integration 200`
-   `spectrometer start`
    *   **Description**: Initiates a spectrometer measurement. This command typically uses the settings configured in the Spectrometer UI panel (integration time, cycles, averages) and interacts with the `SpectrometerDriver` component.
    *   **Example**: `spectrometer start`
-   `spectrometer stop`
    *   **Description**: Stops the current spectrometer measurement if one was initiated by a `spectrometer start` command in the routine.
    *   **Example**: `spectrometer stop`
-   `spectrometer save`
    *   **Description**: Saves the current spectrometer spectrum data (from the live view) to a CSV file. The file is timestamped (e.g., `final_[timestamp].csv`) and saved in the `data/` directory. Metadata, including the routine command itself and a timestamp, is often included as commented lines within the CSV file.
    *   **Example**: `spectrometer save`
-   `data start`
    *   **Description**: Starts the continuous data logging mode (see Section 4.1.5 and 4.4). This is equivalent to clicking the "Start Saving" button in the Spectrometer panel.
    *   **Example**: `data start`
-   `data stop`
    *   **Description**: Stops the continuous data logging mode.
    *   **Example**: `data stop`
-   `plot`
    *   **Description**: Takes a snapshot of the current main spectrometer spectrum. This snapshot is then:
        1.  Saved as a CSV file in the `diagrams/` directory (e.g., `snapshot_[timestamp].csv`).
        2.  Added as a static, colored overlay curve on the main spectrometer plot in the UI. Up to 5 such static overlays are displayed; older ones are removed as new ones are added.
    *   **Example**: `plot`

### 4.4. Data Logging

The software automatically logs various types of data to help track measurements, provide diagnostic information, and for later analysis.

#### 4.4.1. Log Files (`logs/` directory)
- **Purpose**: These are plain text (`.txt`) files intended for debugging, status tracking, and recording a chronological summary of events and hardware messages.
- **Naming Convention**: `log_[timestamp].txt` (e.g., `log_20231027_143000.txt`), where the timestamp indicates when the log was started. A new log file is created each time continuous saving is initiated.
- **Content**:
    - Status messages from various hardware controllers (connection, disconnection, errors).
    - Messages explicitly logged by routines using the `log` command.
    - Messages processed by `MainWindow.handle_status_message`, which often include severity levels (`[INFO]`, `[WARNING]`, `[ERROR]`).
    - During continuous data saving, a summary of each saved spectrometer sample (timestamp and peak intensity) is typically added.
- **Location**: Found in the `logs/` sub-directory within the application's main folder structure.

#### 4.4.2. CSV Data Files (`data/` and `diagrams/` directories)
- **Purpose**: Comma-Separated Values (CSV) files are used for storing detailed, structured data from sensors and the spectrometer. This format is suitable for analysis in spreadsheet software (like Excel, LibreOffice Calc) or data analysis tools (like Python with pandas, R).
- **Types and Naming Conventions**:
    - **Continuous Scans**: `Scans_[timestamp]_mini.csv`
        - **Created**: When continuous data saving is active (toggled via UI or routine).
        - **Location**: `data/` directory.
        - **Content**: Contains a comprehensive set of readings from all active sensors and the full spectrometer spectrum for each save interval. Columns typically include: Timestamp, MotorAngle_deg, FilterPos, Roll_deg, Pitch_deg, Yaw_deg, AccelX_g, AccelY_g, AccelZ_g, MagX_uT, MagY_uT, MagZ_uT, Pressure_hPa (from IMU), TempEnv_C (from IMU), TempCurr_C (from Temp Controller), TempSet_C (from Temp Controller), Latitude, Longitude, IntegTime_us (Spectrometer), THPTemp_C, THPHum_pct, THPPres_hPa, Spec_temp_C (auxiliary temp from Temp Controller), RoutineCode, and Pixel_0, Pixel_1, ... for spectrometer data.
    - **Routine Snapshots / Final Data**: `final_[timestamp].csv`
        - **Created**: By the `spectrometer save` routine command.
        - **Location**: `data/` directory.
        - **Content**: Primarily "Pixel" and "Intensity" columns for a single spectrometer spectrum. May also include metadata written as commented lines (e.g., `# routine_command: spectrometer save`) at the beginning of the file.
    - **Manual Spectrometer "Save" Button Snapshots**: `snapshot_[timestamp].csv`
        - **Created**: When the **Save** button in the Spectrometer panel is clicked.
        - **Location**: `data/` directory.
        - **Content**: "Pixel" and "Intensity" columns for the currently displayed/captured spectrum.
    - **Routine "plot" Command Snapshots (CSV)**: `snapshot_[timestamp].csv`
        - **Created**: By the `plot` routine command.
        - **Location**: `diagrams/` directory.
        - **Content**: "Pixel" and "Intensity" columns for the spectrum snapshot taken at that point in the routine.
        - **Note**: The base filename `snapshot_[timestamp].csv` might collide if manual saves and plot commands occur at the exact same second, though unlikely due to different directories.

### 4.5. Schedule Management (`schedules/` directory)

The `schedules/` directory in the application folder contains text files (e.g., `schedule_po.txt`, `schedule_sg.txt`). These files suggest a feature for scheduling the execution of routines at specific times or intervals.

[**Note to User Manual Author:** The current codebase review did not find explicit UI elements or manager classes for loading and executing these schedules. This feature might be planned, partially implemented, or managed by external scripts. To document this fully, further information from the developers on how users interact with schedules (if at all through this UI) would be required. If it's not a user-configurable feature via this software, this section may need to be adjusted or removed.]

Assuming this feature is user-accessible, a user might need to know:
-   How to create or modify schedule files.
-   The specific syntax used within these schedule files (e.g., how to list routine names, define timings, specify repetitions, or handle dates/times).
-   How to load a schedule into the software and initiate its execution.
-   How to monitor and stop a running schedule.

## 5. Hardware Control Panels

The right-hand panel of the main window contains several group boxes for controlling individual hardware components. Each panel typically includes a connection status indicator in its title.

### 5.1. General: Connection Indicators
Each hardware control panel (Spectrometer, Motor, Filter Wheel, IMU, Temperature Controller, THP Sensor) displays a colored dot (●) in its title bar to indicate the connection status:
-   **Green Dot (●)**: The hardware component is connected and presumed to be operational.
-   **Red Dot (●)**: The hardware component is not connected, or an error occurred during connection or operation.

Check the main Status Bar for more detailed messages regarding connection errors.

### 5.2. Motor Controller
-   **Panel Title**: "Motor"
-   **UI Elements**:
    -   **COM Port**: Dropdown menu to select or manually enter the COM port for the motor.
    -   **Connect/Disconnect Button**: Toggles the connection to the motor. The software will attempt to auto-detect the correct baud rate.
    -   **Preset (°)**: Dropdown menu to select a preset angle (0° to 360° in 30° increments). Selecting a preset automatically populates the "Custom (°)" field and triggers a motor move if the motor is connected.
    -   **Custom (°)**: Text input field to specify a custom target angle in degrees.
    -   **Move Button**: Commands the motor to move to the angle specified in the "Custom (°)" field. This button is enabled only when the motor is connected.
-   **Functionality**:
    -   **Auto-Connect**: Attempts to connect to the motor on the port specified in `hardware_config.json` at startup.
    -   **Initial Move**: Automatically moves the motor to 0° upon a successful connection.
    -   **Manual Movement**: Allows users to move the motor to precise angles using either preset or custom values.
-   **Status Display**: While there isn't a dedicated display for the motor's current angle in its panel, successful moves and the target angle are reported in the main Status Bar. The "Custom (°)" field also reflects the last commanded angle.

### 5.3. Filter Wheel Controller
-   **Panel Title**: "Filter Wheel"
-   **UI Elements**:
    -   **COM Port**: Dropdown menu to select or enter the COM port.
    -   **Connect/Disconnect Button**: Toggles the connection.
    -   **Pos:**: Label displaying the current detected filter position (e.g., "1", "2", or "--" if unknown or not connected).
    -   **Open Button**: Moves the filter wheel to a predefined "open" filter position (typically position 2).
    -   **Opaque Button**: Moves the filter wheel to a predefined "opaque" filter position (typically position 1; this is also the reset position).
    -   **Diff Button** (Diffuser): Moves the filter wheel to a predefined "diffuser" filter position (typically position 5).
    -   **Cmd LineEdit**: Input field for sending raw commands directly to the filter wheel (for advanced users).
    -   **Send Button**: Sends the raw command entered in the "Cmd" field.
-   **Functionality**:
    -   **Auto-Connect**: Attempts to connect on startup if the port is configured in `hardware_config.json`.
    -   **Initial Position**: Automatically resets to position 1 (Opaque) upon successful connection.
    -   **Filter Selection**: Provides quick buttons for commonly used filter types/positions.
    -   **Manual Control**: Allows direct command input for specific filter positions not covered by the quick buttons or for other filter wheel commands.
-   **Status Display**: The "Pos:" label shows the current filter position. All operations and their outcomes are reported in the main Status Bar.

### 5.4. IMU (Inertial Measurement Unit) Controller
-   **Panel Title**: "IMU"
-   **UI Elements**:
    -   **COM Port**: Dropdown menu to select or enter the COM port.
    -   **Baud**: Dropdown menu to select the communication baud rate (e.g., 9600, 57600, 115200), which must match the IMU device's configuration.
    -   **Connect/Disconnect Button**: Toggles the connection.
    -   **Data Display Label**: Shows a formatted table of the latest IMU readings, including:
        -   Roll, Pitch, Yaw (in degrees)
        -   Temperature (from IMU sensor, in °C)
        -   Pressure (in hPa)
        -   Latitude, Longitude (GPS coordinates, if the IMU provides them)
-   **Functionality**:
    -   **Auto-Connect**: Attempts to connect on startup if the port is configured in `hardware_config.json`.
    -   **Data Refresh**: Once connected, IMU data is read by a background thread. The displayed data updates automatically approximately every 100 milliseconds (10 Hz).
-   **Status Display**: Connection status is shown by the indicator dot and messages in the main Status Bar. Sensor data is displayed directly in the panel.

### 5.5. Temperature Controller
-   **Panel Title**: "Temperature Controller"
-   **UI Elements**:
    -   **COM Port**: Dropdown menu to select or enter the COM port.
    -   **Connect/Disconnect Button**: Toggles the connection.
    -   **Current Label**: Displays the current temperature from the primary sensor of the temperature controller (e.g., "20.50 °C").
    -   **Auxiliary Label**: Displays the current temperature from an auxiliary sensor, if available (e.g., "21.00 °C"). This often corresponds to the spectrometer's internal temperature sensor if managed by the same controller.
    -   **Set Temperature Label** & **Setpoint SpinBox**: Allows setting the target temperature for the controller (e.g., range 15.0 to 40.0 °C, with 0.5°C steps).
    -   **Set Button**: Applies the new temperature setpoint to the controller.
-   **Functionality**:
    -   **Auto-Connect**: Attempts to connect on startup if the port is configured in `hardware_config.json` (or uses a default like "COM16" if not specified).
    -   **Power Control**: Automatically enables computer control mode and powers on the thermoelectric (TE) device upon connection. When disconnecting via the UI, power to the TE device is turned off.
    -   **Temperature Monitoring**: Displays primary and auxiliary temperatures, which are updated periodically (approximately every 1 second).
    -   **Setpoint Control**: Allows users to define and set the desired operational temperature.
-   **Status Display**: Connection status, setpoint confirmations, and any read errors are shown in the main Status Bar. Temperatures are displayed directly in the panel.

### 5.6. THP (Temperature, Humidity, Pressure) Sensor
-   **Panel Title**: "THP Sensor"
-   **UI Elements**:
    -   **Port Label**: Displays the configured COM port for the THP sensor (this is not user-editable directly in this panel; it's initially set via `hardware_config.json`).
    -   **Reconnect Button**: Manually triggers a new attempt to read data from the sensor. This can be useful if communication was temporarily lost.
    -   **Readings Label**: Displays current Temperature (°C), Humidity (%), and Pressure (hPa) from the sensor.
-   **Functionality**:
    -   **Configuration**: Uses the port specified in `hardware_config.json` (passed during initialization).
    -   **Automatic Reading**: Data is read periodically (approximately every 3 seconds), and the display updates with the latest values.
    -   **Manual Refresh**: The **Reconnect** button allows for an immediate manual refresh of the sensor data.
-   **Status Display**: Connection status is shown by the indicator dot and messages in the main Status Bar. Sensor readings are displayed directly in the panel. If reads fail, the panel will indicate a connection or sensor issue.

## 6. Troubleshooting

This section provides guidance on common issues and how to resolve them.

### 6.1. Hardware Connection Issues
-   **Symptom**: Red status indicator (●) on a hardware panel; status bar messages like "Device not found," "No response from...," "Failed to connect...," or COM port errors.
-   **Possible Causes & Solutions**:
    -   **Physical Connections**: Double-check that the device is securely plugged into the computer (USB) and powered on (if it has external power). Try a different USB cable or port.
    -   **Correct COM Port**: Verify the correct COM port is selected in the device's control panel within the software.
        -   On Windows, you can find assigned COM ports in Device Manager under "Ports (COM & LPT)".
        -   On Linux, devices might appear as `/dev/ttyUSB0`, `/dev/ttyACM0`, etc.
        -   On macOS, look for `/dev/cu.usbserial-*` or similar.
    -   **`hardware_config.json`**: If you are relying on automatic connections at startup, ensure the COM port specified in your `hardware_config.json` file for the problematic device is accurate for your current setup.
    -   **COM Port in Use**: Another application might be exclusively using the COM port. Close any other software that might be connected to the device (this includes previous instances of Mini ROBOHyPO, other sensor monitoring tools, or serial terminal programs like PuTTY).
    -   **Hardware Drivers**: Ensure that drivers for your USB-to-Serial adapters (e.g., FTDI, CH340) or specific hardware (like the Avantes spectrometer SDK) are correctly installed and up to date on your operating system.
    -   **Baud Rate (IMU)**: For the IMU controller specifically, ensure the correct baud rate is selected in its control panel, as this must match the IMU device's configured communication speed.
    -   **Restart Application**: After checking connections and drivers, try restarting the Mini ROBOHyPO software.
    -   **Device Power Cycle**: For some hardware, power cycling the device itself (turning it off and then on again) can resolve temporary communication glitches.

### 6.2. Errors During Routine Execution
-   **Routine Hangs or Stops Prematurely**:
    -   A `wait [time_ms]` command in the routine might have an excessively long duration.
    -   A hardware command (e.g., `motor move`, `filter position`) might not be completing if the hardware encounters an issue or does not acknowledge the command. While many routine steps use fixed delays, a hardware fault could prevent subsequent actions.
    -   Check the main Status Bar for any error messages from the specific hardware command that might have failed.
    -   You can use the **Stop** button in the "Routine Control" panel to manually halt a hanging or problematic routine.
-   **Command Errors Displayed**:
    -   The **Routine Status** display (e.g., "Running command X/Y...") might show an error related to a specific command.
    -   The main Status Bar or the console output (if you launched the application from a terminal) may provide more detailed error messages.
    -   Carefully check the syntax of your routine file (`.txt`) for typos, incorrect command names, or invalid parameters (e.g., `motor move seventy` instead of `motor move 70`, or a filter position out of range).
-   **Unexpected Hardware Behavior During Routine**:
    -   If hardware doesn't behave as expected (e.g., motor moves to an incorrect angle, filter doesn't change), first try to operate the hardware manually using its dedicated control panel in the UI. This helps determine if the issue is with the hardware/connection itself or with the routine's command.
    -   Verify that the parameters used in the routine command (e.g., angle, filter position number) are correct and within the device's operational limits.

### 6.3. Application Not Responding or Freezing
-   **Hardware Communication Timeout/Hang**: If a hardware device stops responding while the software is trying to communicate with it (especially during a blocking call, though the software uses threads for many operations), the UI might become sluggish or appear to freeze.
    -   Try to identify which hardware might be causing the issue (e.g., was a command just sent to a specific device?).
    -   If possible, try disconnecting the suspected hardware device via its UI panel (if the UI is still partially responsive).
    -   Check the `logs/` directory for error messages after restarting the application.
-   **Error Dialog**: If a critical error occurs, an error dialog (often titled "Application Error") may appear with technical details. This dialog might pause the main application until it is closed. Note down the information provided in this dialog if you need to report the issue.
-   **Consistent Freezes**: If the application consistently freezes at a particular step or during a specific operation, note the sequence of actions leading up to the freeze. This information, along with log files, is crucial for debugging. You may need to restart the application.

### 6.4. Spectrometer Issues
-   **No Data / Plot is Empty**:
    -   **Connection**: Ensure the spectrometer is connected (green indicator in its panel, "Spectrometer ready" status message). Try the **Connect/Disconnect** button.
    -   **Measurement Active**: Check if a measurement is actually active (the **Stop** button should be enabled, and the **Start** button disabled).
    -   **Light Source / Path**: Ensure your light source is on and correctly aligned with your sample and the spectrometer's input optics. The light path might be blocked.
    -   **Integration Time**: The integration time might be too short for the current light level, resulting in very low counts that appear as no data. Try significantly increasing the integration time.
    -   **Parameters**: Verify that "Cycles" and "Repetitions" are set to reasonable values (e.g., at least 1).
-   **Noisy Data / Unstable Spectrum**:
    -   **Integration Time**: Too short an integration time is a common cause of noisy data. Increase it to collect more photons and improve the signal-to-noise ratio.
    -   **Averaging**: Ensure averaging is being used. For short integration times, the software attempts some automatic software averaging. You can also increase hardware averaging using the "Cycles" setting.
    -   **Light Source Stability**: A fluctuating light source will cause an unstable spectrum.
    -   **Optical Alignment**: Ensure all optical components (fibers, lenses, sample) are properly aligned and secured.
    -   **Ambient Light**: If your setup is not light-tight, changes in ambient room light can introduce noise or affect measurements.
    -   **Temperature**: Spectrometer performance can be temperature-dependent. Ensure the spectrometer is within its operational temperature range. The Temperature Controller panel may show the spectrometer's internal temperature (often as "Auxiliary").
-   **Connection Problems (Specific to Spectrometer)**:
    -   **"No spectrometer found" / "AVS_Init error" / "Error opening spectrometer"**:
        -   Check the USB connection to the spectrometer thoroughly.
        -   Ensure the Avantes SDK drivers are correctly installed on your system.
        -   Make sure the required Avantes DLL files (e.g., `avaspec.dll`, `avaspecx64.dll`) are accessible to the application (see Section 2.2).
        -   Try a different USB port or a different USB cable.
    -   **"Spectrometer already in use"**: Another program might be using the spectrometer. Close any other instances of Mini ROBOHyPO or other Avantes-related software.
    -   The software attempts to auto-connect on startup and will retry if the initial connection attempt fails. Monitor the Status Bar for messages.

### 6.5. Interpreting Log Files for Errors
-   **Location**: Log files are stored in the `logs/` directory within the application's folder, named `log_[timestamp].txt`.
-   **Content**: These files contain timestamped entries that can include:
    -   Status messages from various hardware components (e.g., connection attempts, success, failure).
    -   Error messages reported by hardware drivers or controllers (e.g., "Failed to connect...", "No ACK received", "Sensor error...").
    -   Messages explicitly logged by routines via the `log` command.
    -   Messages often include severity prefixes like `[INFO]`, `[WARNING]`, or `[ERROR]`, which help in quickly identifying the nature of the entry.
-   **Usage for Troubleshooting**:
    -   When an issue occurs, open the most recent log file (or the one corresponding to the session where the error happened).
    -   Search for entries around the time the error was observed.
    -   Look specifically for lines containing `ERROR` or `WARNING` as these often provide direct clues about the problem's origin (e.g., which device failed, the type of error).
    -   Even `INFO` messages can be helpful to understand the sequence of operations leading up to an error.

## 7. Frequently Asked Questions (FAQ)

**Q1: How do I know if the hardware is connected correctly?**
A1: Each hardware control panel in the UI has a colored dot (●) in its title bar:
    *   A **Green Dot** indicates that the software believes the device is connected and operational.
    *   A **Red Dot** indicates that the device is not connected, or an error occurred during the last connection attempt or operation.
    Additionally, the main Status Bar at the bottom of the window will display messages about successful connections (e.g., "Motor connected on COM11") or connection failures.

**Q2: Where is my data saved?**
A2: Data is saved in subdirectories within the application's main folder:
    *   **Continuous Data Logging**: `Scans_[timestamp]_mini.csv` (for detailed sensor and spectral data) are saved in the `data/` directory. Corresponding summary log files `log_[timestamp].txt` are saved in the `logs/` directory.
    *   **Single Spectrometer Scans (using "Save" button)**: `snapshot_[timestamp].csv` files are saved in the `data/` directory.
    *   **Routine "spectrometer save" Command**: `final_[timestamp].csv` files (spectral data with metadata) are saved in the `data/` directory.
    *   **Routine "plot" Command Snapshots**: The spectral data for these snapshots is saved as `snapshot_[timestamp].csv` in the `diagrams/` directory. The `ResultsPlotDialog` (e.g., after PO routine) also saves its plot as a PNG image in the `diagrams/` directory.

**Q3: Can I create my own routines? How?**
A3: Yes, you can create custom routines:
    1.  Routines are plain text files (usually with a `.txt` extension).
    2.  You can create a new `.txt` file, for example, in the `routines/` directory (or any location you prefer).
    3.  Write your sequence of commands in this file, with one command per line. Refer to **Section 8.1: Routine Command Reference** for the list of available commands and their syntax.
    4.  Use the `#` symbol at the beginning of a line to add comments (which are ignored during execution).
    5.  Save your routine file.
    6.  In the Mini ROBOHyPO software, go to the **Routine Control** panel and click the **Load File** button.
    7.  In the file dialog that opens, navigate to and select your custom `.txt` routine file.
    8.  Once loaded (its name should appear in the Routine Status display), click the **Run Code** button to execute it.

**Q4: What do the different colors in the spectrometer plot mean?**
A4:
    *   **Main Live Spectrum**: The continuously updating spectrum is typically plotted with a solid red line and a light red shaded area underneath it.
    *   **Static Snapshot Overlays**: When the `plot` command is used within a routine, it captures the current spectrum and overlays it on the main plot as a static line. Each such snapshot is drawn with a different, randomly generated color to help distinguish multiple snapshots from each other and from the live spectrum. The plot might also show a legend entry for these snapshots (e.g., "Snapshot [timestamp]").

**Q5: The application crashed. What should I do?**
A5:
    1.  **Error Dialog**: If an "Application Error" dialog appears with details (exception type, message, and a traceback), please copy or take a screenshot of all this information. This is extremely valuable for diagnosing the problem.
    2.  **Log Files**: Check the most recent log file(s) in the `logs/` directory. These files might contain error messages or a sequence of events that occurred just before the crash.
    3.  **Console Output**: If you launched the application from a terminal or command prompt (`python main.py`), look for any error messages printed in that console window.
    4.  **Steps to Reproduce**: Note down the specific actions or sequence of operations you were performing in the software just before the crash occurred. If you can reliably reproduce the crash with the same steps, this is very helpful.
    5.  **Restart**: Try restarting the application. If it crashes again under the same circumstances, it indicates a reproducible bug.
    6.  **Report the Issue**: Provide all the gathered information (error dialog details, relevant log file sections, console output, and steps to reproduce) to the software developers or your designated support contact for assistance.

## 8. Appendix

### A.1. Routine Command Reference

The following commands can be used in routine (`.txt`) files. Command keywords (e.g., `log`, `wait`) are generally case-insensitive. Parameters enclosed in `<angle brackets>` are placeholders for values that you must provide.

*   `log <message>`
    *   **Description**: Displays the `<message>` in the main window's status bar and also prints it to the application's console output (if visible). This is useful for indicating the current stage of a routine or logging custom information.
    *   **Example**: `log Starting filter sweep operation`

*   `wait <time_ms>`
    *   **Description**: Pauses routine execution for the specified `<time_ms>` in milliseconds.
    *   **Example**: `wait 1500` (This will pause the routine for 1.5 seconds)

*   `motor move <angle>`
    *   **Description**: Commands the Motor Controller to move the motor to the specified `<angle>`. The angle is interpreted in degrees.
    *   **Example**: `motor move 45.0`

*   `filter position <position_number>`
    *   **Description**: Commands the Filter Wheel Controller to set the filter wheel to the specified `<position_number>`. Position numbers are typically integers (e.g., 1 through 6).
    *   **Example**: `filter position 1`

*   `integration <time_ms>`
    *   **Description**: Sets the spectrometer's integration time to `<time_ms>` milliseconds. This action updates the integration time setting in the Spectrometer UI panel and applies it to the main spectrometer. If a measurement is currently active on the main spectrometer, it might be stopped and restarted to apply the new integration time.
    *   **Example**: `integration 100`

*   `spectrometer start`
    *   **Description**: Starts a spectrometer measurement. This command primarily interacts with the `SpectrometerDriver` component within the `SpectrometerController`. The measurement parameters (like integration time, cycles, averaging) used by this command path are typically those configured in the UI for the `SpectrometerDriver` or default driver settings, which might differ from the main UI's direct control path if not synchronized.
    *   **Example**: `spectrometer start`

*   `spectrometer stop`
    *   **Description**: Stops an ongoing spectrometer measurement that was initiated by a `spectrometer start` command in the routine.
    *   **Example**: `spectrometer stop`

*   `spectrometer save`
    *   **Description**: Saves the current spectrometer spectrum data (obtained from the main `SpectrometerController`'s live data buffer, `self.intens`) to a CSV file. The file is automatically timestamped (e.g., `final_[timestamp].csv`) and saved in the `data/` directory. The CSV file includes metadata such as the routine command that triggered the save and a timestamp, typically written as commented lines (`#`) at the beginning of the file.
    *   **Example**: `spectrometer save`

*   `data start`
    *   **Description**: Starts the continuous data logging mode. This is equivalent to clicking the "Start Saving" button in the Spectrometer UI panel and will create timestamped CSV and TXT log files in the `data/` and `logs/` directories, respectively, capturing data from all active and configured sensors.
    *   **Example**: `data start`

*   `data stop`
    *   **Description**: Stops the continuous data logging mode if it is currently active.
    *   **Example**: `data stop`

*   `plot`
    *   **Description**: This command performs two actions:
        1.  Takes a snapshot of the current main spectrometer spectrum data.
        2.  Saves this snapshot to a CSV file in the `diagrams/` directory (e.g., `snapshot_[timestamp].csv`).
        3.  Adds this spectrum as a static, colored overlay curve on the main spectrometer plot in the UI. The software keeps up to the last 5 such static overlays; older ones are removed as new ones are added.
    *   **Example**: `plot`

**Note on Additional Hardware Commands:**
The `RoutineManager`'s `_execute_command` method, as reviewed, directly implements the commands listed above. If functionality to control other specific hardware parameters via routines is needed (e.g., `temp set <temperature>`, `thp read`, `camera capture <filename>`), these commands would need to be explicitly added to the `RoutineManager`'s parsing and execution logic. Currently, such commands are not supported by default.
    *   To set temperature: Use the Temperature Controller panel manually, or ensure the device reaches a stable temperature before starting routines that depend on it.
    *   To read THP: THP data is read automatically and logged if continuous saving is active.
    *   To capture camera images: This is not a built-in routine command.

### A.2. `hardware_config.json` Parameters

The `hardware_config.json` file is used to pre-configure default connection parameters for various hardware devices, primarily their COM ports. This file should be located in the application's main directory and formatted in JSON.

**Primary Use**: Defining default COM ports for serial (COM port based) devices to simplify initial setup.

**Parameters**:

*   `"filterwheel": "<COM_PORT_STRING>"`
    *   **Description**: Specifies the COM port for the Filter Wheel controller.
    *   **Example**: On Windows: `"COM12"`. On Linux: `"/dev/ttyUSB0"`.
*   `"imu": "<COM_PORT_STRING>"`
    *   **Description**: Specifies the COM port for the IMU.
    *   **Example**: `"COM14"`
*   `"motor": "<COM_PORT_STRING>"`
    *   **Description**: Specifies the COM port for the Motor controller.
    *   **Example**: `"COM11"`
*   `"temp_controller": "<COM_PORT_STRING>"`
    *   **Description**: Specifies the COM port for the Temperature Controller.
    *   **Example**: `"COM13"`
*   `"thp_sensor": "<COM_PORT_STRING>"`
    *   **Description**: Specifies the COM port for the THP (Temperature, Humidity, Pressure) sensor.
    *   **Example**: `"COM10"`

**Note on Spectrometer Configuration**:
The `hardware_config.json` file, as per the reviewed codebase, does not contain specific operational settings for the spectrometer (such as default integration time, averaging parameters, or specific spectrometer serial number to connect to if multiple are present).
*   The spectrometer connection logic (`drivers.spectrometer.connect_spectrometer`) attempts to connect to the first available Avantes spectrometer found on USB.
*   Operational parameters like integration time are managed through the Spectrometer UI panel or set via routine commands like `integration <time_ms>`.
