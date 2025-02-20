import sys
import time
from threading import Thread 
from socket import *
from pathlib import Path

# Input validation
if len(sys.argv) != 2:
    print("\n=== Usage: python3 client.py SERVER_port ===\n")
    exit(0)

# Extract input
serverHost = '127.0.0.1'
serverPort = int(sys.argv[1])
serverAddress = (serverHost, serverPort)

# Setup UDP socket for server communication
udp_socket = socket(AF_INET, SOCK_DGRAM)
udp_socket.connect(serverAddress)

# Add this after UDP socket setup
# Setup TCP server socket for file transfers
tcp_server = socket(AF_INET, SOCK_STREAM)
tcp_server.bind(('127.0.0.1', 0))  # Use random available port
tcp_server.listen(5)
tcp_port = tcp_server.getsockname()[1]  # Get the assigned port


# Authenticate with the server
def authenticate():
    while True:
        username = input("Enter username: ")
        password = input("Enter password: ")
        # tcp_port = 0  # Placeholder, will be assigned later

        # Prepare message for authentication
        message = f"AUTH {username} {password} {tcp_port}"
        udp_socket.sendto(message.encode(), serverAddress)

        # Receive response from the server
        response, _ = udp_socket.recvfrom(1024)
        if response.decode() == "OK":
            print("Welcome to BitTrickle!")
            print("Available commands are: get, lap, lpf, pub, sch, unp, xit")
            return username
        else:
            print("Authentication failed. Please try again.")

# Send heartbeats periodically
def send_heartbeats(username):
    while True:
        udp_socket.sendto(f"HBT {username}".encode(), serverAddress)
        time.sleep(2)


# Add these new functions for file transfer
def handle_file_upload(conn, filename):
    try:
        with open(filename, 'rb') as f:
            data = f.read(1024)
            while data:
                conn.send(data)
                data = f.read(1024)
    except Exception as e:
        print(f"Error uploading file: {e}")
    finally:
        conn.close()


# Handle client commands
def handle_commands(username):
    while True:
        command = input("> ").strip()
        
        if command.startswith("get"):
            if len(command.split()) > 1:
                filename = command.split(maxsplit=1)[1]
                
                udp_socket.sendto(f"GET {username} {filename}".encode(), serverAddress)
                response, _ = udp_socket.recvfrom(1024)
                response_text = response.decode()
                
                if response_text == "File not found":
                    print(response_text)
                else:
                    download_thread = Thread(target=download_file, args=(filename, response_text))
                    download_thread.daemon = True  # Make thread exit when main program exits
                    download_thread.start()
                    download_thread.join()
            else:
                print("Usage: get <filename>")


        elif command == "lap":
            if len(command.split()) == 1:
                udp_socket.sendto(f"LAP {username}".encode(), serverAddress)
                response, _ = udp_socket.recvfrom(1024)
                print(response.decode())
            else:
                print("Usage: lap")
        
        elif command == "lpf":
            if len(command.split()) == 1:  
                udp_socket.sendto(f"LPF {username}".encode(), serverAddress)
                response, _ = udp_socket.recvfrom(1024)
                print(response.decode())
            else:
                print("Usage: lpf")
            
        elif command.startswith("pub"):
            if len(command.split()) == 2:  
                filename = command.split(maxsplit=1)[1]
                udp_socket.sendto(f"PUB {username} {filename}".encode(), serverAddress)
                response, _ = udp_socket.recvfrom(1024)
                print(response.decode())
            else:
                print("Usage: pub <filename>")
            
        elif command.startswith("sch"):
            if len(command.split()) == 2:
                substring = command.split(maxsplit=1)[1] 
                udp_socket.sendto(f"SCH {username} {substring}".encode(), serverAddress)
                response, _ = udp_socket.recvfrom(1024)
                print(response.decode())
            else:
                print("Usage: sch <substring>")
                
        elif command.startswith("unp"):
            if len(command.split()) == 2:  
                filename = command.split(maxsplit=1)[1] 
                udp_socket.sendto(f"UNP {username} {filename}".encode(), serverAddress)
                response, _ = udp_socket.recvfrom(1024)
                print(response.decode())
            else:
                print("Usage: unpub <filename>")
            
        elif command == "xit":
            print("Goodbye!")
            udp_socket.close()
            exit(0)
        else:
            print("Unknown command. Available commands: get, lap, lpf, pub, sch, unp, xit")


# Modify handle_file_upload
def handle_file_upload(conn, filename):
    try:
        file_path = Path(filename)
        if file_path.exists():
            with file_path.open('rb') as f:
                data = f.read(1024)
                while data:
                    conn.send(data)
                    data = f.read(1024)
    except Exception as e:
        print(f"Error uploading file: {e}")
    finally:
        conn.close()

def handle_incoming_connections():
    while True:
        try:
            conn, addr = tcp_server.accept()
            filename = conn.recv(1024).decode()
            file_path = Path(filename)
            if file_path.exists():
                Thread(target=handle_file_upload, args=(conn, filename)).start()
        except Exception as e:
            print(f"Error accepting connection: {e}")

def download_file(filename, peer_address):
    try:
        host, port = peer_address.split(':')
        tcp_client = socket(AF_INET, SOCK_STREAM)
        tcp_client.connect((host, int(port)))
        
        # Send filename request
        tcp_client.send(filename.encode())
        
        download_path = Path(f"{filename}")
        with download_path.open('wb') as f:
            while True:
                data = tcp_client.recv(1024)
                if not data:
                    break
                f.write(data)
        print(f"{download_path} downloaded successfully")
    except Exception as e:
        print(f"Error downloading file: {e}")
    finally:
        tcp_client.close()

# Main function
def main():
    username = authenticate()
    
    # Start heartbeat thread
    heartbeat_thread = Thread(target=send_heartbeats, args=(username,))
    heartbeat_thread.daemon = True
    heartbeat_thread.start()

    # Start TCP server thread
    tcp_thread = Thread(target=handle_incoming_connections)
    tcp_thread.daemon = True
    tcp_thread.start()

    # Handle user commands
    handle_commands(username)
    
if __name__ == "__main__":
    main()
