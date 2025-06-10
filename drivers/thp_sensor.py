import serial
import json
import time

def read_thp_sensor_data(port_name, baud_rate=9600, timeout=1):
    ser = None  # Initialize ser to None
    try:
        ser = serial.Serial(port_name, baud_rate, timeout=timeout)
        # time.sleep(1) # This delay might be long; test if shorter/removable.
                      # Some devices need a moment after port open before ready.
                      # For robust communication, a loop that tries to send/receive a
                      # handshake or waits for a specific ready signal is better than a fixed sleep.
                      # Keeping it for now as it might be there for a specific hardware reason.
        time.sleep(0.2) # Reduced delay, assuming it might be sufficient.

        ser.reset_input_buffer()
        ser.write(b'p\r\n') # Send command to request data

        response = ""
        start_time = time.time()
        # Read loop to accumulate response, attempting to parse JSON incrementally
        while time.time() - start_time < timeout: # Loop with overall timeout
            if ser.in_waiting > 0:
                # Read available bytes, decode, and append to response buffer
                # Using read_all() or read(ser.in_waiting) can be more efficient than readline() here
                # if the JSON response is not strictly line-terminated before being complete.
                # However, readline() is fine if each part of response or full response ends with newline.
                try:
                    # Attempt to read a line, assuming JSON parts might be line-terminated or
                    # the full JSON response is followed by a newline.
                    line = ser.readline().decode('utf-8', errors='replace').strip()
                    if line: # Append if something was read
                        response += line
                        # Try to parse the accumulated response. If it's valid JSON, we are done.
                        data = json.loads(response)
                        break # Successfully parsed JSON
                    # If line is empty, it might be a timeout from readline itself, loop will continue by main timeout
                except json.JSONDecodeError:
                    # Incomplete JSON, or malformed. Continue accumulating if time allows.
                    if time.time() - start_time >= timeout: # Check timeout immediately after read attempt
                        break # Overall timeout exceeded
                    continue
                except serial.SerialException as se_read: # Catch specific serial errors during read
                    print(f"THP sensor error during read on {port_name}: {se_read}")
                    return None # Exit on serial error
            else: # No data in buffer
                if time.time() - start_time >= timeout: # Check overall timeout
                    break
                time.sleep(0.05) # Small pause to prevent busy-waiting if no data
        else: # Loop completed without break (either timeout or successful parse)
            if not response: # Explicitly check if response is still empty after loop
                print(f"THP sensor error: No response from sensor on {port_name} after read loop.")
                return None
        
        # After loop, try to parse the final accumulated response one last time
        # This handles cases where JSON was valid only at the very end of accumulation.
        # If json.loads(response) succeeded in the loop, 'data' will already be populated.
        # If the loop timed out and 'response' might be a complete JSON, this will parse it.
        if 'data' not in locals() or data is None: # If not parsed in loop
            try:
                data = json.loads(response)
            except json.JSONDecodeError:
                 # If still not parsable, means it's either incomplete or malformed.
                if response: # Only print error if there was some response
                    print(f"THP sensor error: Final JSON parsing failed on {port_name}. Response: {repr(response)}")
                else: # This case should be caught by the 'if not response:' check above.
                    print(f"THP sensor error: No response received on {port_name}.")
                return None

        # If we got no response at all (this check is now mostly covered by loop logic)
        if not response:
            print(f"THP sensor error: No response from sensor on {port_name}")
            return None
            
        # Try to parse the final response
        # Process the successfully parsed 'data'
        sensors = data.get('Sensors', [])
        if sensors:
            s = sensors[0] # Assuming we only care about the first sensor in the list
            return {
                'sensor_id': s.get('ID'),
                'temperature': s.get('Temperature'),
                'humidity': s.get('Humidity'),
                'pressure': s.get('Pressure')
            }
        else:
            print(f"THP sensor error: 'Sensors' array missing or empty in JSON response from {port_name}. Response: {data}")
            return None

    except serial.SerialTimeoutException as ste: # Specific timeout on port open or initial config
        print(f"THP sensor error: Serial timeout on {port_name}: {ste}")
        return None
    except serial.SerialException as se: # Other serial port errors (e.g., port not found)
        print(f"THP sensor error: SerialException on {port_name}: {se}")
        return None
    except json.JSONDecodeError as je: # Should be caught by internal logic, but as a safeguard
        print(f"THP sensor error: Final JSON decoding failed on {port_name}: {je}. Response: {repr(response if 'response' in locals() else 'N/A')}")
        return None
    except Exception as e: # Catch-all for other unexpected errors
        print(f"THP sensor error: Unexpected error on {port_name}: {e}")
        return None
    finally:
        if ser and ser.is_open:
            ser.close()

