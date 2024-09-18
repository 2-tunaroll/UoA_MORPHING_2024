import serial
import time

# Initialize serial connection to Arduino
ser = serial.Serial('/dev/ttyACM0', 57600, timeout=1)

# Send motor commands (example: set motor 1 velocity to 100 RPM)
def send_motor_command(motor_id, command_type, value):
    command = f'{motor_id} {command_type} {value}\n'
    ser.write(command.encode())
    time.sleep(0.1)

# Example: Set motor 1 to velocity 100 RPM
send_motor_command(1, 2, 100)

# Example: Set motor 7 to position 180 degrees
send_motor_command(2, 1, 180)

ser.close()
