from XInputPython.XInputTest import *

import socket
import time
import struct

# Server settings
#host = 'Raspberry_Pi_IP_Address'  # Replace with the IP address of your Raspberry Pi
#port = 12345

# Create a socket object
#client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect to the server
#client_socket.connect((host, port))

def get_controller_position(data):
    print(data)
    return data  # Placeholder return value

try:
    while True:
        # Get the position list from your script
        #position = get_controller_position()

        # Pack the float and integer into a binary format
        #message = struct.pack('!fi', position[0], position[1])

        # Send the message to the server
        #client_socket.sendall(message)
        pass
        # Add a delay to simulate real-time transmission
        #time.sleep(1)  # Adjust the delay as needed

except KeyboardInterrupt:
    print("Client interrupted")

finally:
    # Close the connection
    #client_socket.close()
    pass

print(get_trigger_values())