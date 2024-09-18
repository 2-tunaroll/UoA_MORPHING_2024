import serial
import time

# Open serial communication with the OpenRB-150 via /dev/ttyACM0
ser = serial.Serial('/dev/ttyACM0', 57600, timeout=1)
time.sleep(2)  # Wait for the Arduino to initialize

# Send a test message to the OpenRB-150
def send_test_data(data):
    command = f'{data}\n'
    print(f"DEBUG: Sending data: {command.strip()}")
    ser.write(command.encode())

send_test_data("Hello OpenRB-150")
ser.close()