import serial
import time

# Initialize serial connection to Arduino
try:
    ser = serial.Serial('/dev/ttyACM0', 57600, timeout=1)
    print("DEBUG: Successfully opened serial port /dev/ttyACM0.")
except serial.SerialException as e:
    print(f"ERROR: Could not open serial port - {e}")
    exit(1)

# Function to send motor control commands
def send_motor_command(motor_id, command_type, value):
    command = f'{motor_id} {command_type} {value}\n'
    try:
        print(f"DEBUG: Sending command: {command.strip()}")
        ser.write(command.encode())
        print("DEBUG: Command sent successfully.")
    except Exception as e:
        print(f"ERROR: Failed to send command - {e}")

# Example: Send motor command
try:
    send_motor_command(1, 2, 100)  # Motor 1, Set velocity, 100 RPM
except KeyboardInterrupt:
    print("DEBUG: Keyboard interrupt received. Exiting...")
finally:
    print("DEBUG: Closing the serial port.")
    ser.close()
