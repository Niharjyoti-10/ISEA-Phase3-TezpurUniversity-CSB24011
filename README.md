# Assignment 7 – Secure GUI-Based TCP Chat Application

**Student:** Niharjyoti Choudhury  
**Roll Number:** CSB24011  
**Program:** Networking Internship, Phase 3 – Tezpur University

---

# Objective

Enhance the GUI-based TCP chat application developed in Assignment 6 by incorporating
essential security mechanisms used in real-world client-server systems. The application
implements secure username-password authentication, SHA-256 password hashing,
duplicate login prevention, failed login protection, input validation, session management,
secure event logging, and Wireshark-based verification of the underlying TCP
communication.

---

# Software Requirements

| Component | Purpose |
|-----------|---------|
| Ubuntu Linux (VirtualBox) | Host operating system |
| Python 3 | Programming language |
| Tkinter | GUI framework |
| Socket Programming (`socket`) | TCP client-server communication |
| hashlib | SHA-256 password hashing |
| JSON | Secure user credential storage |
| Multithreading (`threading`) | Concurrent client handling |
| Mininet | Network topology emulation |
| Wireshark | TCP packet capture and analysis |
| Visual Studio Code | Development environment |

---

# Network Topology

The application was tested inside Mininet using a single-switch topology with one
server host and two client hosts.

```bash
sudo mn --topo single,3
```

| Host | Role |
|------|------|
| h1 | Secure TCP Chat Server (`server.py`) |
| h2 | Client A (`client_gui.py`) |
| h3 | Client B (`client_gui.py`) |

All hosts communicate through a single Open vSwitch (`s1`).
Connectivity was verified using:

```bash
nodes
net
pingall
```

before launching the server and clients.

---

# Execution Steps

### 1. Start Mininet

```bash
sudo mn --topo single,3
```

### 2. Open terminals

```bash
mininet> xterm h1 h2 h3
```

### 3. Start the server

```bash
python3 server.py
```

### 4. Start the GUI clients

```bash
python3 client_gui.py
```

### 5. Login

Enter:

- Server IP
- Username
- Password

Click **Connect**.

### 6. Broadcast Message

Type a message and press **Send**.

### 7. Private Message

```
/msg <username> <message>
```

Example

```
/msg user1 Hello
```

### 8. Logout

Click the **Logout** button.

### 9. Wireshark Capture

Capture packets on

```
s1-eth1
```

using

```
tcp.port == 5000
```

---

# Security Features

The following security mechanisms were implemented.

- Username and Password Authentication
- SHA-256 Password Hashing
- Secure Password Storage (`users.json`)
- Duplicate Login Prevention
- Failed Login Protection
- Temporary Account Blocking
- Username Validation
- Password Validation
- Unsupported Command Detection
- Message Length Validation
- Session Timeout
- Secure Event Logging
- Broadcast Messaging
- Private Messaging
- Online User Tracking

---

# Sample Screenshots

## Server Startup

![Server](screenshots/server_initialization.png)

---

## Login Window

![Login](screenshots/login_interface.png)

---

## Successful Authentication

![Login Success](screenshots/successfull_authentication.png)

---

## Broadcast Messaging

![Broadcast](screenshots/broadcast_communication.png)

---

## Private Messaging

![Private](screenshots/private_messaging.png)

---

## Online Users

![Users](screenshots/online_users_list.png)

---

## Duplicate Login Prevention

![Duplicate Login](screenshots/duplicate_login_prevention.png)

---

## Authentication Failure

![Authentication Failed](screenshots/invalid_login.png)

---

## Account Blocking

![Blocked](screenshots/account_blocking.png)

---

## Unsupported Command Validation

![Unsupported Command](screenshots/unsupported_command.png)

---

## Session Timeout

![Session Timeout](screenshots/session_timeout.png)

---

## Wireshark – TCP Connection Establishment

![Wireshark Login](screenshots/wireshark_server_initialization.png)

---

## Wireshark – Broadcast Communication

![Broadcast](screenshots/wireshark_broadcast_messaging.png)

---

## Wireshark – Private Message Communication

![Private](screenshots/wireshark_private_messaging.png)

---

## Wireshark – TCP Connection Termination

![Termination](screenshots/wireshark_connection_termination.png)

---

# Implementation Overview

### `server.py`

Implements the secure multi-client TCP chat server. The server authenticates users
using SHA-256 hashed passwords stored in `users.json`, prevents duplicate logins,
handles multiple clients using threads, validates user input, records security events,
maintains active sessions, supports broadcast and private messaging, and automatically
logs out inactive users after the configured timeout period.

---

### `client_gui.py`

Implements a Tkinter-based graphical client. The application provides a login window
for username-password authentication followed by a chat interface consisting of a
scrollable chat area, message entry box, Send button, Logout button, and a live
online-user list. A background receiver thread continuously updates the GUI without
blocking user interaction.

---

### Authentication System

Authentication is performed using username-password credentials. Passwords are never
stored in plain text. Instead, SHA-256 hashing is used to securely verify user
credentials against entries stored in `users.json`.

---

### Input Validation

The application validates all user input including:

- Empty usernames
- Empty passwords
- Invalid usernames
- Unsupported commands
- Oversized messages

Invalid input is rejected before processing.

---

### Session Management

The server maintains active user sessions, prevents multiple simultaneous logins using
the same account, supports manual logout, and automatically terminates inactive
sessions after the configured timeout.

---

### Secure Logging

Security-related events are stored in `security_log.txt`, including:

- Server startup
- Authentication attempts
- Successful logins
- Failed logins
- Duplicate login attempts
- Account blocking
- Logout events
- Session timeout

---

### Wireshark Verification

The secure chat application was tested inside Mininet. Wireshark packet captures
confirmed successful TCP three-way handshake, user authentication, broadcast
communication, private messaging, and graceful TCP connection termination using
FIN/ACK packets.

---

# Learning Outcomes

Through this assignment, the following concepts were learned:

- Secure Socket Programming
- Authentication and Authorization
- Password Hashing using SHA-256
- Secure Credential Storage
- Session Management
- Input Validation
- Multi-threaded Client-Server Communication
- TCP Packet Analysis using Wireshark
- Secure Software Development Practices

---

# Technologies Used

- Python 3
- Tkinter
- Socket Programming
- Threading
- JSON
- hashlib (SHA-256)
- Mininet
- Wireshark
- Visual Studio Code

---

# Repository Structure

```
Assignment7/
│
├── server.py
├── client_gui.py
├── users.json
├── security_log.txt
├── screenshots/
├── README.md
└── report.pdf
```

---

# Author

**Niharjyoti Choudhury**  
Roll Number: **CSB24011**  
Department of Computer Science and Engineering  
Tezpur University

---

# License

This project was developed for educational purposes as part of **Networking Internship – Phase 3 (Assignment 7)** at **Tezpur University**.
