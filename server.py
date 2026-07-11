import socket
import threading
import csv
import os
from datetime import datetime

HOST = "0.0.0.0"
PORT = 5000

clients = {}
client_info = {}

lock = threading.Lock()

TOTAL_MESSAGES = 0
BROADCAST_MESSAGES = 0
PRIVATE_MESSAGES = 0
TEST_START = None
TEST_END = None

CHAT_FILE = "chat_history.csv"
PERFORMANCE_FILE = "performance_results.csv"

if not os.path.exists(CHAT_FILE):
    with open(CHAT_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "timestamp",
            "sender",
            "receiver",
            "message_type",
            "message"
        ])

if not os.path.exists(PERFORMANCE_FILE):
    with open(PERFORMANCE_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "clients",
            "broadcast_messages",
            "private_messages",
            "avg_delay_ms",
            "throughput_msgs_per_sec"
        ])


def save_history(sender, receiver, msg_type, message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(CHAT_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            timestamp,
            sender,
            receiver,
            msg_type,
            message
        ])


def get_last_messages(username):
    messages = []

    if not os.path.exists(CHAT_FILE):
        return messages

    with open(CHAT_FILE, "r") as f:
        reader = csv.DictReader(f)

        for row in reader:
            if row["sender"] == username:
                messages.append(
                    f'{row["timestamp"]} -> {row["message"]}'
                )

    return messages[-5:]


def broadcast(message, sender=None):
    global TOTAL_MESSAGES
    global BROADCAST_MESSAGES

    TOTAL_MESSAGES += 1
    BROADCAST_MESSAGES += 1

    remove_list = []

    with lock:
        for user, sock in clients.items():
            if user != sender:
                try:
                    sock.send(message.encode())
                except:
                    remove_list.append(user)

        for user in remove_list:
            clients.pop(user, None)


def private_message(sender, receiver, message):
    global TOTAL_MESSAGES
    global PRIVATE_MESSAGES

    TOTAL_MESSAGES += 1
    PRIVATE_MESSAGES += 1

    if receiver not in clients:
        clients[sender].send("User not found.\n".encode())
        return

    text = f"[PRIVATE] {sender}: {message}"

    clients[receiver].send(text.encode())
    clients[sender].send(
        f"[You -> {receiver}]: {message}".encode()
    )
    save_history(
        sender,
        receiver,
        "PRIVATE",
        message
    )


def send_online_users(username):
    users = ",".join(clients.keys())
    text = f"ONLINE:{users}"

    clients[username].send(text.encode())

def update_online_users():
    users = ",".join(clients.keys())
    text = f"ONLINE:{users}"

    remove_list = []

    with lock:
        for user, sock in clients.items():
            try:
                sock.send(text.encode())
            except:
                remove_list.append(user)

        for user in remove_list:
            clients.pop(user, None)

def print_stats():
    print()

    print("========== SERVER ==========")
    print("Connected Users :", len(clients))
    print("Total Messages  :", TOTAL_MESSAGES)
    print("Broadcast Msgs  :", BROADCAST_MESSAGES)
    print("Private Msgs    :", PRIVATE_MESSAGES)
    print("============================")
    print()


def save_performance():

    if TEST_START is None or TEST_END is None:
        return

    elapsed = (TEST_END - TEST_START).total_seconds()

    if elapsed <= 0:
        elapsed = 0.001

    clients_count = len(client_info)

    throughput = TOTAL_MESSAGES / elapsed

    avg_delay = (elapsed / TOTAL_MESSAGES) * 1000 if TOTAL_MESSAGES else 0

    with open(PERFORMANCE_FILE, "a", newline="") as f:

        writer = csv.writer(f)

        writer.writerow([
            clients_count,
            BROADCAST_MESSAGES,
            PRIVATE_MESSAGES,
            round(avg_delay, 2),
            round(throughput, 2)
        ])


def handle_client(conn, addr):
    global TEST_START
    global TEST_END

    username = ""

    try:
        conn.send("Enter username: ".encode())

        username = conn.recv(1024).decode().strip()

        with lock:
            clients[username] = conn
            client_info[username] = {
                "ip": addr[0],
                "port": addr[1],
                "login_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status": "Online"
            }

        print(f"{username} connected from {addr[0]}:{addr[1]}")

        conn.send("\nWelcome to the Chat Server!\n".encode())

        history = get_last_messages(username)

        if history:
            conn.send("\nLast 5 messages:\n".encode())

            for msg in history:
                conn.send((msg + "\n").encode())

        broadcast(f"SYSTEM: {username} joined the chat.", username)

        update_online_users()

        print_stats()

        while True:

            message = conn.recv(4096).decode()

            if not message:
                break

            message = message.strip()

            if message == "":
                continue

            if message.startswith("/msg"):

                parts = message.split(" ", 2)

                if len(parts) < 3:
                    conn.send(
                        "Usage: /msg <username> <message>\n".encode()
                    )
                    continue

                receiver = parts[1]
                text = parts[2]

                private_message(
                    username,
                    receiver,
                    text
                )

                continue

            if message == "/list":

                send_online_users(username)

                continue

            if TEST_START is None:
                TEST_START = datetime.now()

            text = f"{username}: {message}"

            broadcast(text, username)

            save_history(
                username,
                "ALL",
                "BROADCAST",
                message
            )

            TEST_END = datetime.now()

            print(text)

    except Exception as e:
        print(e)

    finally:

        with lock:

            if username in clients:
                del clients[username]

            if username in client_info:
                client_info[username]["status"] = "Offline"

        broadcast(f"SYSTEM: {username} left the chat.")
        update_online_users()
        print(f"{username} disconnected.")
        print_stats()

        if len(clients) == 0:
            save_performance()

        conn.close()


def start_server():

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server.bind((HOST, PORT))

    server.listen()

    print("=" * 40)
    print("TCP Chat Server Started")
    print(f"Listening on {HOST}:{PORT}")
    print("=" * 40)

    while True:

        conn, addr = server.accept()

        thread = threading.Thread(
            target=handle_client,
            args=(conn, addr)
        )

        thread.daemon = True

        thread.start()


if __name__ == "__main__":
    start_server()
