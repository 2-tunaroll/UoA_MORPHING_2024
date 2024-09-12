#sudo apt-get update
#sudo apt-get install python3-serial
#pip3 install pyserial


#Open the Raspberry Pi configuration tool:
#bash
#sudo raspi-config
#Navigate to Interfacing Options -> Serial.
#Disable the login shell over serial and enable the serial port hardware.

import serial
import time

ser = serial.Serial('/dev/ttyUSB0', 9600)  # Adjust the port as necessary

def send_data(data):
    formatted_data = ','.join(map(str, data)) + '\n'
    ser.write(formatted_data.encode())

data_to_send = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]

while True:
    send_data(data_to_send)
    print(f"Sent: {data_to_send}")
    time.sleep(1)

ser.close()