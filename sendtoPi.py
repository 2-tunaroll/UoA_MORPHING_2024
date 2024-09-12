import socket
import struct

server_ip = 'Raspberry_Pi_IP'  # Replace with the Raspberry Pi's IP address
server_port = 65432

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((server_ip, server_port))

try:
    while True:
        # Replace this with your real-time values
        int_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
        # Pack the data
        packed_data = struct.pack('11i', *int_list)
        client_socket.sendall(packed_data)

except KeyboardInterrupt:
    print("Interrupted by user")
finally:
    client_socket.close()