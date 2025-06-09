import mysql.connector
import re
import socket
import struct
import random
from collections import deque

FLAGS = {
    'SYN': 0b00000010,
    'ACK': 0b00010000,
    'FIN': 0b00000001
}

WINDOW_SIZE = 10  # fixed window size
ring_buffer = deque(maxlen=5)

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
    print(f"{'Window Size':<15}{fields[5]}")
    print(f"{'Checksum':<15}{fields[6]}")
    print("="*30)

def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="tcp_chat"
    )

def validate_username(username):
    return (re.search(r'[A-Z]', username) and
            re.search(r'[a-z]', username) and
            re.search(r'[0-9]', username) and
            re.search(r'[!@#$%^&*(),.?":{}|<>]', username))

def validate_password(password):
    return password.isdigit() and len(password) == 5

def register():
    conn = connect_db()
    cursor = conn.cursor()

    username = input("Enter new username: ")
    password = input("Enter 5-digit numeric password: ")

    if not validate_username(username):
        print("Username must include capital, small, number, and special char.")
        return False

    if not validate_password(password):
        print("Password must be exactly 5 digits.")
        return False

    try:
        cursor.execute("INSERT INTO clients (username, password) VALUES (%s, %s)", (username, password))
        conn.commit()
        print("Registration successful!\n")
        return True
    except mysql.connector.errors.IntegrityError:
        print("Username already exists.")
        return False
    finally:
        conn.close()

def login():
    conn = connect_db()
    cursor = conn.cursor()

    username = input("Username: ")
    password = input("Password: ")

    cursor.execute("SELECT * FROM clients WHERE username=%s AND password=%s", (username, password))
    result = cursor.fetchone()
    conn.close()

    if result:
        print("✅ Login successful!\n")
        return True
    else:
        print("❌ Credentials not matched.\n")
        return False

def calculate_data_length(message):
    return sum(1 for c in message if c.isalnum() or c.isspace())

def client():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(("", 12345))

    seq_num = random.randint(100, 999)
    syn_header = create_tcp_header(54321, 12345, seq_num, 0, FLAGS['SYN'])
    client_socket.send(syn_header)
    print("Sent SYN to server.")

    syn_ack = client_socket.recv(1024)
    print("Received SYN-ACK from server.")
    print_tcp_header(syn_ack)

    ack_num = struct.unpack('!HHIIHHHH', syn_ack)[2] + 1
    seq_num += 1
    final_ack_header = create_tcp_header(54321, 12345, seq_num, ack_num, FLAGS['ACK'])
    client_socket.send(final_ack_header)
    print("Sent final ACK. Connection established!\n")
    print_tcp_header(final_ack_header)

    while True:
        message = input("You: ")
        data_len = calculate_data_length(message)
        seq_num += data_len

        client_socket.send(message.encode())
        ring_buffer.append(f"You: {message}")

        # Show TCP header for sent message
        msg_header = create_tcp_header(54321, 12345, seq_num, ack_num, FLAGS['ACK'])
        print_tcp_header(msg_header)

        response = client_socket.recv(1024).decode()
        print(f"Server: {response}")
        ring_buffer.append(f"Server: {response}")

        data_len = calculate_data_length(response)
        ack_num += data_len

        # Show TCP header for ACKing server's message
        response_header = create_tcp_header(54321, 12345, seq_num, ack_num, FLAGS['ACK'])
        print_tcp_header(response_header)

        if response.lower() == "exit":
            print("Server exited. Closing connection.")
            break

    print("\nConversation history (ring buffer):")
    for msg in ring_buffer:
        print(msg)

    client_socket.close()

def main():
    while True:
        print("Welcome to TCP Chat Client")
        print("1. Login")
        print("2. New Client")
        print("3. Exit")
        choice = input("Choose option: ")

        if choice == "1":
            if login():
                client()
                break
        elif choice == "2":
            register()
        elif choice == "3":
            break
        else:
            print("Invalid choice. Try again.\n")

if __name__ == "__main__":
    main()