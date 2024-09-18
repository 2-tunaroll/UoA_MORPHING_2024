import serial
import time

try:
    # Initialize serial connection to OpenRB-150
    ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
    time.sleep(2)  # Give some time for the connection to establish

    if ser.is_open:
        print("DEBUG: Serial port opened successfully.")
    else:
        print("ERROR: Failed to open serial port.")
except Exception as e:
    print(f"ERROR: Could not open serial port - {e}")
    exit(1)

# Function to send data and read response
def send_test_data(data):
    command = f'{data}\n'
    try:
        print(f"DEBUG: Sending: {command.strip()}")
        ser.write(command.encode())  # Send the command
        time.sleep(1)  # Wait for Arduino to process the command

        # Read the response from the Arduino
        response = ser.readline().decode().strip()
        if response:
            print(f"DEBUG: Received: {response}")
        else:
            print("DEBUG: No response from Arduino.")
    except Exception as e:
        print(f"ERROR: Failed to communicate with Arduino - {e}")

# Send data
send_test_data("Hello from Pi")

# Close the serial connection
ser.close()
