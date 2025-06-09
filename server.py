# === SERVER CODE ===
import socket
import struct
import random
from collections import deque

FLAGS = {
    'SYN': 0b00000010,
    'ACK': 0b00010000,
    'FIN': 0b00000001
}

WINDOW_SIZE = 10
RING_BUFFER_SIZE = 5
ring_buffer = deque(maxlen=RING_BUFFER_SIZE)

def count_valid_characters(data):
    return sum(c.isalnum() or c.isspace() for c in data)

def calculate_checksum(data):
    return sum(data) % 65535

def create_tcp_header(source_port, dest_port, seq_num, ack_num, flags, window_size=WINDOW_SIZE):
    offset_res_flags = (5 << 12) | flags
    checksum = calculate_checksum(struct.pack('!II', seq_num, ack_num))
    return struct.pack('!HHIIHHHH', source_port, dest_port, seq_num, ack_num, offset_res_flags, window_size, checksum, 0)

def print_tcp_header(header):
    fields = struct.unpack('!HHIIHHHH', header)
    print("\nTCP HEADER DETAILS:")
    print(f"{'Field':<15}{'Value'}")
    print("="*30)
    print(f"{'Source Port':<15}{fields[0]}")
    print(f"{'Dest Port':<15}{fields[1]}")
    print(f"{'Seq Num':<15}{fields[2]}")
    print(f"{'Ack Num':<15}{fields[3]}")
    print(f"{'Flags':<15}{bin(fields[4] & 0b111111)}")
    print(f"{'Checksum':<15}{fields[6]}")
    print(f"{'Window Size':<15}{fields[5]}")
    print("="*30)

def server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("172.23.233.36", 12345))
    server_socket.listen(1)
    print("Waiting for client to connect...")

    conn, addr = server_socket.accept()
    print(f"Client {addr} connected.")

    syn_header = conn.recv(1024)
    client_seq = struct.unpack('!HHIIHHHH', syn_header)[2]
    print("[Handshake] Received SYN from client.")
    print_tcp_header(syn_header)

    server_seq = random.randint(2000, 9999)
    ack_num = client_seq + 1
    syn_ack_header = create_tcp_header(12345, 54321, server_seq, ack_num, FLAGS['SYN'] | FLAGS['ACK'])
    conn.send(syn_ack_header)
    print("[Handshake] Sent SYN-ACK.")
    print_tcp_header(syn_ack_header)

    final_ack = conn.recv(1024)
    print("[Handshake] Received final ACK. Connection established!\n")
    print_tcp_header(final_ack)

    while True:
        data = conn.recv(1024).decode()
        if not data:
            break

        ring_buffer.append(data)
        data_length = count_valid_characters(data)
        print(f"Client: {data}")

        server_seq += data_length
        header = create_tcp_header(12345, 54321, server_seq, ack_num, FLAGS['ACK'])
        print_tcp_header(header)

        response = input("You: ")
        if response.strip() == "":
            continue

        conn.send(response.encode())
        server_seq += count_valid_characters(response)

        if response.lower() == "exit":
            break

    conn.close()
    server_socket.close()

if __name__ == "__main__":
    server()
