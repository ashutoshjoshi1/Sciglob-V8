import serial
from PyQt5.QtCore import QThread, pyqtSignal
import utils

# Motor control constants for Oriental Motor AZ series (Modbus)
TrackerSpeed = 10000       # Motor rotation speed (steps/s)
TrackerCurrent = 1000      # Motor current limit (in 0.1% units, 1000 = 100.0%)
SlaveID = 2                # Modbus slave address of the motor controller
BaudRateList = [9600, 19200, 38400, 57600, 115200, 230400]

class MotorConnectThread(QThread):
    """Thread to attempt motor serial connection with baud auto-detection."""
    result_signal = pyqtSignal(object, int, str)  # will emit (serial_obj or None, baud_rate, message)
    def __init__(self, port_name, parent=None):
        super().__init__(parent)
        self.port_name = port_name
    def run(self):
        found_serial = None
        found_baud = None
        message = ""
        # Try each baud rate to find a responding motor
        for baud in BaudRateList:
            try:
                ser = serial.Serial(
                    self.port_name, baudrate=baud, bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_EVEN, stopbits=serial.STOPBITS_ONE,
                    timeout=0.5
                )
                # Example Modbus read command (function 0x03) at register 0x0058 (2 registers)
                base_cmd = bytes([SlaveID, 0x03, 0x00, 0x58, 0x00, 0x02])
                crc_val = utils.modbus_crc16(base_cmd)
                crc_bytes = crc_val.to_bytes(2, 'little')
                ser.write(base_cmd + crc_bytes)
                # Read a few bytes to detect any response
                response = ser.read(5)
                if response:
                    found_serial = ser
                    found_baud = baud
                    message = f"Motor connected on {self.port_name} at {baud} baud."
                    break
                ser.close()
            except Exception:
                # Ignore exceptions and try next baud
                continue
        if not found_serial:
            message = f"No response from motor on {self.port_name}."
        # Emit result (serial object if found, else None)
        self.result_signal.emit(found_serial, found_baud if found_baud else 0, message)

def send_move_command(serial_obj, angle: int) -> bool:
    """
    Send a move command to the motor to go to the specified angle (in motor steps).
    Returns True if ACK received, False otherwise.
    This constructs a Modbus RTU frame for function code 0x10 (Write Multiple Registers).
    The command structure is specific to the Oriental Motor AZ series for a particular type of move.
    """
    # Modbus RTU Command Structure:
    # Slave ID: 1 byte (self.SlaveID)
    # Function Code: 1 byte (0x10 for Write Multiple Registers)
    # Starting Address: 2 bytes (e.g., 0x0058 for operation data setting)
    # Number of Registers: 2 bytes (e.g., 0x0012 for 18 registers)
    # Byte Count: 1 byte (e.g., 0x24 for 36 bytes of data)
    # Data: N bytes (register values)
    # CRC: 2 bytes

    # Example: Operation Data Setting (No.1 Data) - Refer to AZ Series Modbus RTU Manual
    # Register 0x0058: Data No. (1 = Data No.1) - 2 registers (long)
    # Register 0x005A: Method (0 = Absolute, 1 = Relative) - 2 registers (long)
    # Register 0x005C: Position (steps) - 2 registers (long)
    # Register 0x005E: Speed (Hz) - 2 registers (long)
    # Register 0x0060: Accel/Decel Rate 1 (ms) - 2 registers (long)
    # Register 0x0062: Accel/Decel Rate 2 (ms) - 2 registers (long)
    # Register 0x0064: Push-motion current limit (%) - 2 registers (long)
    # Register 0x0066: Trigger setting - 2 registers (long)
    # ... and more registers up to 18 for this specific command (0x0012 registers = 36 bytes)

    # This base_cmd appears to be for a specific "Direct Operation" or similar,
    # where subsequent data bytes for angle, speed, current are directly part of the payload.
    # The exact register mapping for this specific command should be verified with the motor's manual.
    # The command below seems to be setting Data No.1 (0x00000001) and then other parameters.
    # The structure implies fixed values for some parts of the operation.
    base_cmd_header = bytes([
        SlaveID,    # Slave Address
        0x10,       # Function Code: Write Multiple Registers
        0x00, 0x58, # Starting Address (e.g., 0x0058 for Data No.1 Operation Command)
        0x00, 0x12, # Number of Registers (18 registers = 36 bytes)
        0x24        # Byte Count (36 bytes of data)
    ])

    # Data payload construction (36 bytes total)
    # Data No.1: (fixed to 1 in this command example)
    data_no_bytes = (1).to_bytes(4, 'big', signed=False) # 0x00000001

    # Position (Angle in steps)
    try:
        angle_bytes = angle.to_bytes(4, 'big', signed=True) # Target position
    except OverflowError:
        # Clamp angle to 32-bit signed range if out of bounds
        val = max(min(angle, 0x7FFFFFFF), -0x80000000)
        angle_bytes = val.to_bytes(4, 'big', signed=True)
    # Speed
    speed_bytes = TrackerSpeed.to_bytes(4, 'big', signed=False) # Target speed

    # Accel/Decel settings (example fixed values, check manual for meaning)
    # These likely correspond to Accel Rate 1 / Decel Rate 1, Accel Rate 2 / Decel Rate 2
    # Or specific acceleration/deceleration values if the registers map directly.
    # For example, 0x00001F40 = 8000. If these are rates, units are important (e.g. ms, Hz/s).
    # Assuming these are fixed for this command type:
    accel_decel_1_bytes = (8000).to_bytes(4, 'big', signed=False) # e.g., 0x00001F40
    accel_decel_2_bytes = (8000).to_bytes(4, 'big', signed=False) # e.g., 0x00001F40

    # Current / Push-motion current limit
    current_bytes = TrackerCurrent.to_bytes(4, 'big', signed=False) # Operating current

    # Trigger / Other settings (example fixed values)
    # These bytes likely set other operational parameters like trigger conditions,
    # push-motion enable, etc. These should be verified against the manual for this command.
    # The original `base_cmd` had some of these embedded.
    # Reconstructing based on typical AZ series "Direct Operation Data" structure.
    # This part requires careful mapping to the AZ series Modbus documentation for registers
    # starting from 0x0058 if this is a "write data then execute" type of command.
    # The original command had many fixed bytes after the header.
    # Let's assume the original fixed bytes were part of the data payload.
    # Original `base_cmd` started with: SlaveID, 0x10, 0x00, 0x58, 0x00, 0x12, 0x24
    # followed by: 0x00, 0x00, 0x00, 0x01 (Data No.1)
    # then: 0x00, 0x00, 0x00, 0x01 (Method: 1 = relative? or some other fixed param)
    # This indicates the original `base_cmd` was incomplete or structured differently.
    # The provided `base_cmd` was:
    # bytes([SlaveID, 0x10, 0x00, 0x58, 0x00, 0x12, 0x24,  <-- header
    #       0x00, 0x00, 0x00, 0x01,  <-- Data No. (fixed to 1)
    #       0x00, 0x00, 0x00, 0x01]) <-- This could be "Method" or another parameter.
    # This is 8 bytes of data. Total data is 36 bytes. 36 - 8 = 28 bytes remaining.
    # angle_bytes (4) + speed_bytes (4) + mid_bytes (8) + current_bytes (4) + end_bytes (8) = 28 bytes.
    # So, the original structure was: header + fixed_data_part1 + angle + speed + mid_bytes + current + end_bytes

    fixed_data_part1 = bytes([0x00, 0x00, 0x00, 0x01]) # Corresponds to Data No. = 1
    fixed_data_part2 = bytes([0x00, 0x00, 0x00, 0x01]) # Corresponds to Method or another setting

    # mid_bytes and end_bytes from original code, their meaning needs to be verified from manual
    # mid_bytes likely contains Accel/Decel values or other control words
    mid_bytes = bytes([0x00, 0x00, 0x1F, 0x40, 0x00, 0x00, 0x1F, 0x40])
    # end_bytes likely contains trigger settings or command execution flags
    end_bytes = bytes([0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01])

    # Construct the full data payload (36 bytes)
    data_payload = (
        fixed_data_part1 +  # Data No. (4 bytes)
        fixed_data_part2 +  # Method / Other (4 bytes)
        angle_bytes +       # Position (4 bytes)
        speed_bytes +       # Speed (4 bytes)
        mid_bytes +         # Accel/Decel or other params (8 bytes)
        current_bytes +     # Current (4 bytes)
        end_bytes           # Trigger/Execute or other params (8 bytes)
    )

    full_cmd = base_cmd_header + data_payload

    # Append CRC16
    crc_val = utils.modbus_crc16(full_cmd) # CRC is calculated on the whole command (SlaveID to end of data)
    crc_bytes = crc_val.to_bytes(2, 'little')
    try:
        serial_obj.reset_input_buffer()
        serial_obj.write(full_cmd + crc_bytes)
        # Response for function 0x10 (Write Multiple Registers) should be 8 bytes (including CRC)
        response = serial_obj.read(8)
        if response and len(response) >= 6 and response[1] == 0x10:
            return True
        else:
            return False
    except Exception:
        return False

