from socket import *
from threading import Thread, Lock
import sys
import time
from datetime import datetime

# Verify input
if len(sys.argv) != 2:
    print("\n=== Usage: python3 server.py SERVER_PORT ===\n")
    exit(0)

# Extract server host and port
serverHost = "127.0.0.1"
serverPort = int(sys.argv[1])
serverAddress = (serverHost, serverPort)

# Setup UDP socket for the server
udp_socket = socket(AF_INET, SOCK_DGRAM)
udp_socket.bind(serverAddress)

# Load credentials from the file
def load_credentials(filename):
    credentials = {}
    try:
        with open(filename, 'r') as file:
            for line in file:
                username, password = line.strip().split(maxsplit=1)
                credentials[username] = password
    except Exception as e:
        print(f"Error loading credentials: {e}")
    return credentials

credentials = load_credentials("credentials.txt")
active_peers = {}
active_peers_lock = Lock()
publish_files = {}
publish_files_lock = Lock()

# Helper function to print logs with timestamp
def server_print(port, order, username):
    current_time = datetime.now().strftime("%H:%M:%S.%f")[:-3] 
    if order == "OK":
        print(f"{current_time}: {port}: Sent {order} to {username}")
    elif order == "HBT":
        print(f"{current_time}: {port}: Received {order} from {username}")
    else:
        print(f"{current_time}: {port}: Sent ERR to {username}")

def log_message(client_port, message_type, username, receivedOrSent, response):
    current_time = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    if (receivedOrSent == "received"):
        print(f"{current_time}: {client_port}: Received {message_type} from {username}")
    else:
        if (response == "OK"):
            print(f"{current_time}: {client_port}: Sent {response} to {username}")
        else:
            print(f"{current_time}: {client_port}: Sent ERR to {username}")


# Function to handle client messages
def handle_client(message, client_address):
    parts = message.decode().split(maxsplit=1)
    command = parts[0]
    username = parts[1].split(" ")[0]
    log_message(client_address[1], command, username, "received", "OK")
    if command == "AUTH":
        handle_authentication(parts[1], client_address)
    elif command == "HBT":
        handle_heartbeat(client_address)
    elif command == "LAP":
        list_active_peers(client_address, username)
    elif command == "LPF":
        list_published_files(client_address, username)
    elif command.startswith("PUB"):
        filename = parts[1].split(" ")[1]
        publish_file(filename, client_address, username)
    elif command.startswith("SCH"):
        substring = parts[1].split(" ")[1]
        search_files(substring, client_address, username)
    elif command.startswith("UNP"):
        filename = parts[1].split(" ")[1]
        unpublish_file(filename, client_address, username)
    elif command.startswith("GET"):
        filename = parts[1].split(" ")[1]
        get_file(filename, client_address, username)
    else:
        udp_socket.sendto("Invalid command".encode(), client_address)

def get_file(filename, client_address, username):
    matching_user = None
    response = "File not found"
    
    with publish_files_lock:
        for user, files in publish_files.items():
            if user != username:
                if filename in files:
                    matching_user = user
                    break
    
    if not matching_user:
        udp_socket.sendto(response.encode(), client_address)
        log_message(client_address[1], "GET", username, "Sent", "ERR")
    else:
        with active_peers_lock:
            if matching_user in active_peers:
                peer_info = active_peers[matching_user]
                # Send back peer's address and TCP port
                response = f"{peer_info['address'][0]}:{peer_info['tcp_port']}"
                udp_socket.sendto(response.encode(), client_address)
                log_message(client_address[1], "GET", username, "Sent", "OK")
            else:
                udp_socket.sendto("File not found".encode(), client_address)
                log_message(client_address[1], "GET", username, "Sent", "ERR")

# Handle authentication
def handle_authentication(data, client_address):
    try:
        username, password, tcp_port = data.split()
        if username in credentials and credentials[username] == password:
            with active_peers_lock:
                if username in active_peers:
                    response = "User already active"
                    log_message(client_address[1], "AUTH", username, "Sent", "ERR")
                    udp_socket.sendto(response.encode(), client_address)
                else:
                    active_peers[username] = {
                        "address": client_address,
                        "tcp_port": tcp_port,
                        "last_heartbeat": time.time()
                    }
                    response = "OK"
                    log_message(client_address[1], "AUTH", username, "Sent", "OK")
                    udp_socket.sendto(response.encode(), client_address)
        else:
            response = "Authentication failed"
            log_message(client_address[1], "AUTH", username, "Sent", "ERR")
            udp_socket.sendto(response.encode(), client_address)
    except Exception as e:
        print(f"Error during authentication: {e}")
        udp_socket.sendto("Error in authentication".encode(), client_address)

# Handle heartbeat messages
def handle_heartbeat(client_address):
    with active_peers_lock:
        for username, details in active_peers.items():
            if details["address"] == client_address:
                details["last_heartbeat"] = time.time()
                break

# List active peers
def list_active_peers(client_address, username):
    with active_peers_lock:
        active_list = [user for user in active_peers if active_peers[user]["address"] != client_address]
        if active_list:
            if len(active_list) == 1:
                response = "1 active peer:\n"
            else:
                response = f"{len(active_list)} active peers:\n"
            response_list = "\n".join(active_list)
            response = response + response_list
        else:
            response = "No active peers"
        udp_socket.sendto(response.encode(), client_address)
        log_message(client_address[1], "LAP", username, "Sent", "OK")
        

def list_published_files(client_address, username):
    files = set()
    with publish_files_lock:
        for item in publish_files:
            if item == username:
                for f in publish_files[item]:
                    files.add(f)
    if len(files) == 0:
        response = "No files published"
    elif len(files) == 1:
        response = f"1 files published:\n{list(files)[0]}"
    else:        
        response = f"{len(files)} files published:\n"
        response = response + '\n'.join(files)

    log_message(client_address[1], "LPF", username, "Sent", "OK")
    udp_socket.sendto(response.encode(), client_address)

def publish_file(filename, client_address, username):
    with publish_files_lock:
        if username not in publish_files:
            publish_files[username] = set()
        publish_files[username].add(filename)
    
    response = f"File {filename} published successfully" 
    udp_socket.sendto(response.encode(), client_address)
    log_message(client_address[1], "PUB", username, "Sent", "OK")
        

def search_files(substring, client_address, username):
    matching_files = []
    with publish_files_lock:
        for user, files in publish_files.items():
            if user == username: continue
            for filename in files:
                if substring in filename:
                    matching_files.append(filename)
    
    if matching_files == []:
        response = "No files found"
    else:
        if len(matching_files) == 1:
            response = f"1 file found:\n{matching_files[0]}"
        else:
            response = f"{len(matching_files)} files found:\n"
            response = response + '\n'.join(matching_files)
    log_message(client_address[1], "SCH", username, "Sent", "OK")
    udp_socket.sendto(response.encode(), client_address)

def unpublish_file(filename, client_address, username):
    response = "File unpublication failed"
    with publish_files_lock:
        if username in publish_files:
            if filename in publish_files[username]:
                publish_files[username].remove(filename)
                response = f"File {filename} unpublished successfully"
                
    if response == "File unpublication failed":
        log_message(client_address[1], "UNP", username, "Sent", "ERR")
    else:        
        log_message(client_address[1], "UNP", username, "Sent", "OK")
    udp_socket.sendto(response.encode(), client_address)

# Remove inactive peers
def remove_inactive_peers():
    while True:
        current_time = time.time()
        with active_peers_lock:
            to_remove = []
            for user, details in active_peers.items():
                if current_time - details["last_heartbeat"] > 3:
                    to_remove.append(user)
            
            for user in to_remove:
                del active_peers[user]
        time.sleep(1)

# Start a thread to remove inactive peers
cleanup_thread = Thread(target=remove_inactive_peers)
cleanup_thread.daemon = True
cleanup_thread.start()

# Main server loop
print("Server is running and listening for incoming messages...")
while True:
    message, client_address = udp_socket.recvfrom(1024)
    client_thread = Thread(target=handle_client, args=(message, client_address))
    client_thread.start()
