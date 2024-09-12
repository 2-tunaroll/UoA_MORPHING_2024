#sudo apt-get update
#sudo apt-get install python3 python3-pip
#pip3 install socket
import socket
import struct

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('0.0.0.0', 65432))  # Listen on all interfaces, port 65432
server_socket.listen(5)

print('Server is listening...')

while True:
    client_socket, addr = server_socket.accept()
    print(f'Connection from {addr} has been established!')

    while True:
        data = client_socket.recv(44)  # 11 integers * 4 bytes each = 44 bytes
        if not data:
            break
        # Unpack the data
        unpacked_data = struct.unpack('11i', data)
        print(f'Received: {unpacked_data}')

    client_socket.close()
