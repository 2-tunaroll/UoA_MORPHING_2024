import serial
import time

# Initialize serial connection to OpenRB-150 via USB
ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
time.sleep(2)  # Wait for the Arduino to initialize

# Function to send data and read response
def send_test_data(data):
    command = f'{data}\n'
    print(f"Sending: {command.strip()}")
    ser.write(command.encode())  # Send the command

    # Wait and read response from Arduino
    time.sleep(1)  # Give Arduino time to respond
    response = ser.readline().decode().strip()
    if response:
        print(f"Received: {response}")
    else:
        print("No response from Arduino.")

send_test_data("Hello from Pi")
ser.close()
