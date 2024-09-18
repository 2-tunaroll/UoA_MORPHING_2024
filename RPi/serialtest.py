import serial
import time

# Initialize serial connection to Arduino
ser = serial.Serial('/dev/ttyACM0', 57600, timeout=1)
time.sleep(2)  # Wait for Arduino to initialize

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
