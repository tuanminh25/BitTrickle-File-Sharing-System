# BitTrickle

## Overview

This project implements BitTrickle, a permissioned, peer-to-peer file sharing system with a centralized indexing server.  It combines client-server and peer-to-peer models.  The system consists of one server and multiple clients:

1.  The server authenticates users, tracks which users store which files, and facilitates file searching and peer connection for direct file transfer.
2.  The client provides a command-shell interface for users to join the network, share files, and retrieve files from other users.

All client-server communication uses UDP. All peer-to-peer (client-to-client) communication uses TCP.

## Key Features

*   **Authentication:** Users must authenticate with the server before joining the network using a credentials file.
*   **Heartbeat Mechanism:** Clients periodically send heartbeat messages to the server to maintain active status.
*   **File Sharing:** Users can publish files they wish to share.
*   **File Discovery:** Users can search for files using substrings and download them from other users.
*   **Peer Discovery:** Users can list active peers in the network.

## How to Use

1.  **Run the server**: 
    ```bash
    python3 server.py <server_port>
    ```
    The server reads credentials from `credentials.txt` in its working directory.

2.  **Run the client(s)**:
    ```bash
    python3 client.py <server_port>
    ```

3.  **Interact with the client**: Use the following commands within the client's command-shell interface:

    *   `get <filename>`: Download a file.
    *   `lap`: List active peers.
    *   `lpf`: List published files.
    *   `pub <filename>`: Publish a file.  Files must be located in the client's working directory.
    *   `sch <substring>`: Search for files.
    *   `unp <filename>`: Unpublish a file.
    *   `xit`: Exit the client.

## Assumptions

*   The credentials file (`credentials.txt`) is in the server's working directory.
*   Files to be published are in the client's working directory.
*   The client and server can be run on the same host.
*   No UDP packets will be lost, corrupted, or re-ordered in transit.

## Example Interaction
client.py 63155

168 09:16:34.185: 53966: Received HBT from yoda Enter username: vader

169 09:16:34.259: 54347: Received AUTH from vader Enter password: sithlord**

170 09:16:34.259: 54347: Sent OK to vader Welcome to BitTrickle!

...
173 09:16:36.708: 54347: Received LPF from vader > lpf

174 09:16:36.708: 54347: Sent OK to vader 3 files published:

...

181 09:16:42.631: 53966: Received SCH from yoda > sch rfc

182 09:16:42.631: 53966: Sent OK to yoda 1 file found:

...

187 09:16:49.936: 53966: Received GET from yoda > get rfc768.txt

188 09:16:49.936: 53966: Sent OK to yoda
...

192 09:16:58.247: 53966: Received HBT from yoda > xit

193 Goodbye! > xit

194 Goodbye!