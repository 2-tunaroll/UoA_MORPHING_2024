import serial
import time

# Replace with your device's serial port (e.g., COM3, /dev/rfcomm0)
serial_port = 'COM11'
baud_rate = 115200  # Set this to the baud rate of your device

# Initialize serial connection
ser = serial.Serial(serial_port, baud_rate, timeout=1)

try:
    while True:
        # Data to send
        data = "Anybody there?"
        
        # Write data to the serial port
        ser.write(data.encode())
        print(f"Sent: {data}")
        
        # Optional: Read response from the device
        response = ser.readline().decode().strip()
        if response:
            print(f"Response: {response}")
        
        # Wait before sending the next message
        time.sleep(1)  # Adjust the delay as needed

except KeyboardInterrupt:
    print("Stopping serial communication...")

finally:
    # Close the serial connection when exiting
    ser.close()
    print("Serial connection closed.")




