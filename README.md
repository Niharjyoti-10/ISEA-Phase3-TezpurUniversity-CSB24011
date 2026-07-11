# GUI Multi Client Chat Application

## Student Details

**Name:** Niharjyoti Choudhury  
**Roll Number:** CSB24011

---

## Project Overview

This project is a GUI-based Multi Client Chat Application developed using Python's Tkinter library and Socket Programming. It allows multiple clients to communicate over a TCP network through a central server.

The application demonstrates GUI programming, event-driven programming, multithreading, and network communication.

---

## Features

- GUI developed using Tkinter
- Multiple clients can connect simultaneously
- Broadcast messaging
- Private messaging using `/msg`
- Online users list
- Connect and Disconnect functionality
- Chat history stored in CSV format
- Performance statistics logging
- Multithreading for smooth GUI operation
- TCP Socket Programming

---

## Technologies Used

- Python 3
- Tkinter
- Socket Programming
- Threading
- CSV Module
- Mininet
- Wireshark

---

## Project Files

```
server.py
client_gui.py
chat_history.csv
performance_results.csv
README.md
report.pdf
```

---

## How to Run

### 1. Start Mininet

```bash
sudo mn --topo single,4
```

### 2. Open terminals

```bash
xterm h1 h2 h3 h4
```

### 3. Start the Server

```bash
python3 server.py
```

### 4. Start the Clients

```bash
python3 client_gui.py
```

### 5. Connect

Server IP:

```
10.0.0.1
```

Enter a username and click **Connect**.

---

## Commands

Broadcast Message

```
Hello Everyone
```

Private Message

```
/msg username Hello
```

Show Online Users

```
/list
```

Disconnect

```
/quit
```

---

## Output Files

- **chat_history.csv** – Stores all chat messages.
- **performance_results.csv** – Stores performance statistics.

---

## Learning Outcomes

- GUI Programming using Tkinter
- Event-driven Programming
- Socket Programming
- Multithreading
- Client-Server Communication
- Network Programming
- File Handling using CSV

---

## Author

**Niharjyoti Choudhury**  
**Roll Number:** CSB24011
