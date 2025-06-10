import serial, time
from PyQt5.QtCore import QThread, pyqtSignal

class FilterWheelCommandThread(QThread):
    """Background thread to send a command to the filter wheel and read its position."""
    result_signal = pyqtSignal(object, str)  # emits (position, status_message)
    def __init__(self, serial_obj, command, parent=None):
        super().__init__(parent)
        self.serial = serial_obj       # an open serial.Serial instance
        self.command = command.strip() # e.g. "F1r", "F15", "F19" or "?"
    def run(self):
        try:
            # Ensure input buffer is clear before sending
            self.serial.reset_input_buffer()
            # Send the command with CR termination
            cmd_str = self.command + "\r"
            self.serial.write(cmd_str.encode('utf-8'))
            # If it's a move/reset command, wait and then query position
            if self.command != "?":
                time.sleep(1.0)  # wait for the wheel to move/reset
                self.serial.reset_input_buffer()      # flush any interim response
                self.serial.write(b"?\r")             # query current position
                time.sleep(0.5)  # additional wait for response
            # Read the response line (with timeout)
            response = self.serial.readline()  # reads until '\n' or timeout
            pos = None
            if response:
                data = response.decode('ascii', errors='ignore').strip()

                # Try to parse position from the (potentially queried) response data first
                try:
                    pos = int(data) if data.isdigit() else None
                except ValueError:
                    pos = None

                # Determine user-friendly status message
                if self.command == "?": # Original command was a query
                    if pos is not None:
                        msg = f"Filter wheel is at position {pos}."
                    else:
                        msg = f"Filter wheel query response: '{data}' (could not parse position)."
                else: # Original command was a move/reset
                    if pos is not None: # Position successfully parsed from query after move/reset
                        msg = f"Filter wheel operation '{self.command}' completed, current position: {pos}."
                    else:
                        # If query after move/reset failed to yield a parsable position,
                        # we can fall back to assuming position from command, or report uncertainty.
                        # For now, let's report the response and the attempted command.
                        msg = f"Filter wheel command '{self.command}' sent. Query response: '{data}'."
                        # Fallback: try to infer from command if query response was not useful
                        if self.command.startswith('F') and len(self.command) >= 2:
                            if self.command.endswith('r'):
                                pos = 1 # Reset assumes position 1
                                msg += f" Assuming position {pos} after reset."
                            elif len(self.command) == 3 and self.command[2].isdigit():
                                try:
                                    pos = int(self.command[2])
                                    msg += f" Assuming position {pos} from command."
                                except ValueError:
                                    pass # pos remains None
            else:
                # No response (e.g. timeout) from the position query
                pos = None # Ensure pos is None
                if self.command == "?":
                    msg = "No response to filter wheel query (timeout)."
                else: # Move/reset command was sent, but position query afterwards timed out
                    msg = f"Command '{self.command}' sent, but no response to position query (timeout)."
                    # Fallback: try to infer from command if query response timed out
                    if self.command.startswith('F') and len(self.command) >= 2:
                        if self.command.endswith('r'):
                            pos = 1
                            msg += f" Assuming position {pos} after reset."
                        elif len(self.command) == 3 and self.command[2].isdigit():
                            try:
                                pos = int(self.command[2])
                                msg += f" Assuming position {pos} from command."
                            except ValueError:
                                pass # pos remains None
            # (Do not close the port here to keep connection alive)
        except Exception as e:
            pos = None # Ensure pos is None on exception
            msg = f"Serial error: {e}"
            # The thread should not close the serial port it received from the controller.
            # The controller is responsible for managing the port's lifecycle.
            # try:
            #     self.serial.close()
            # except:
            #     pass
        # Emit the result (position may be None if failed or unknown)
        self.result_signal.emit(pos, msg)

class FilterWheelConnectThread(QThread):
    """Background thread to open the filter wheel serial port without blocking UI."""
    result_signal = pyqtSignal(object, str)  # emits (serial_obj, status_message)
    def __init__(self, port_name, parent=None):
        super().__init__(parent)
        self.port = port_name
    def run(self):
        try:
            ser = serial.Serial(self.port, baudrate=4800, timeout=1)
            msg = f"Filter wheel connected on {self.port}"
        except Exception as e:
            ser = None
            msg = f"Failed to open {self.port}: {e}"
        self.result_signal.emit(ser, msg)





