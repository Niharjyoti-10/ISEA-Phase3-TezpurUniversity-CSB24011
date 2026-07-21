import socket
import threading
import csv
import os
import json
import hashlib
import time
from datetime import datetime
import re

HOST = "0.0.0.0"
PORT = 5000

MAX_LOGIN_ATTEMPTS = 5
LOGIN_BLOCK_DURATION = 300
SESSION_TIMEOUT = 600
MAX_MESSAGE_SIZE = 4096
MIN_USERNAME_LENGTH = 3
MAX_USERNAME_LENGTH = 20
VALID_USERNAME_PATTERN = r'^[a-zA-Z0-9_]+$'

USERS_FILE = "users.json"
CHAT_FILE = "chat_history.csv"
PERFORMANCE_FILE = "performance_results.csv"
SECURITY_LOG_FILE = "security_log.txt"

clients = {}
client_info = {}
login_attempts = {}
active_sessions = {}

lock = threading.Lock()

TOTAL_MESSAGES = 0
BROADCAST_MESSAGES = 0
PRIVATE_MESSAGES = 0
TEST_START = None
TEST_END = None

def initialize_files():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f:
            default_users = {
                "admin": hashlib.sha256("admin123".encode()).hexdigest(),
                "bhargav": hashlib.sha256("password".encode()).hexdigest()
            }
            json.dump(default_users, f, indent=4)
    
    if not os.path.exists(CHAT_FILE):
        with open(CHAT_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp", "sender", "receiver", "message_type", "message"
            ])
    
    if not os.path.exists(PERFORMANCE_FILE):
        with open(PERFORMANCE_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "clients", "broadcast_messages", "private_messages", 
                "avg_delay_ms", "throughput_msgs_per_sec"
            ])

def log_security_event(event_type, username, details):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {event_type} | User: {username} | {details}\n"
    
    with open(SECURITY_LOG_FILE, "a") as f:
        f.write(log_entry)
    
    print(f"SECURITY: {log_entry.strip()}")

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def validate_username(username):
    if not username or len(username) < MIN_USERNAME_LENGTH or len(username) > MAX_USERNAME_LENGTH:
        return False, "Username must be 3-20 characters long"
    
    if not re.match(VALID_USERNAME_PATTERN, username):
        return False, "Username can only contain letters, numbers, and underscores"
    
    return True, "Valid username"

def validate_message(message):
    if not message or len(message) > MAX_MESSAGE_SIZE:
        return False, f"Message must not exceed {MAX_MESSAGE_SIZE} characters"
    
    dangerous_patterns = [';', '--', '/*', '*/', 'DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER']
    for pattern in dangerous_patterns:
        if pattern in message.upper():
            return False, "Message contains prohibited patterns"
    
    return True, "Valid message"

def authenticate_user(username, password):
    valid, msg = validate_username(username)
    if not valid:
        return False, msg
    
    with open(USERS_FILE, "r") as f:
        users = json.load(f)
    
    if username not in users:
        log_security_event("LOGIN_FAILED", username, "User does not exist")
        return False, "Invalid username or password"
    
    if username in login_attempts:
        attempt_data = login_attempts[username]
        current_time = time.time()
        
        if attempt_data.get("blocked_until") and current_time < attempt_data["blocked_until"]:
            remaining = int((attempt_data["blocked_until"] - current_time) / 60)
            return False, f"Account blocked. Try again in {remaining} minutes"
    
    hashed_password = hash_password(password)
    
    if users[username] == hashed_password:
        if username in login_attempts:
            del login_attempts[username]
        
        log_security_event("LOGIN_SUCCESS", username, "Login successful")
        return True, "Login successful"
    else:
        current_time = time.time()
        
        if username not in login_attempts:
            login_attempts[username] = {
                "attempts": 1,
                "first_attempt": current_time,
                "blocked_until": None
            }
        else:
            login_attempts[username]["attempts"] += 1
            
            if login_attempts[username]["attempts"] >= MAX_LOGIN_ATTEMPTS:
                login_attempts[username]["blocked_until"] = current_time + LOGIN_BLOCK_DURATION
                log_security_event("ACCOUNT_BLOCKED", username, 
                    f"Blocked for {LOGIN_BLOCK_DURATION/60} minutes due to 5 failed attempts")
                return False, f"Account blocked for {LOGIN_BLOCK_DURATION/60} minutes"
        
        log_security_event("LOGIN_FAILED", username, 
            f"Incorrect password. Attempt {login_attempts[username]['attempts']}")
        return False, "Invalid username or password"

def prevent_duplicate_login(username):
    with lock:
        if username in clients:
            if username in active_sessions:
                current_time = time.time()
                if current_time - active_sessions[username] < SESSION_TIMEOUT:
                    return False, "User already logged in"
                else:
                    del active_sessions[username]
                    return True, "Previous session expired"
            return True, "User not currently active"
    return True, "Login allowed"

def check_session_timeout(username):
    if username in active_sessions:
        current_time = time.time()
        if current_time - active_sessions[username] > SESSION_TIMEOUT:
            log_security_event("SESSION_TIMEOUT", username, "Session timed out")
            logout_user(username, "Session timeout")
            return True
    return False

def update_activity(username):
    if username in active_sessions:
        active_sessions[username] = time.time()
    if username in client_info:
        client_info[username]["last_activity"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def logout_user(username, reason="User logged out"):
    with lock:
        if username in clients:
            try:
                clients[username].send("LOGOUT:".encode())
            except:
                pass
            clients[username].close()
            del clients[username]
        
        if username in active_sessions:
            del active_sessions[username]
        
        if username in client_info:
            client_info[username]["status"] = "Offline"
            client_info[username]["logout_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    log_security_event("LOGOUT", username, reason)
    broadcast(f"SYSTEM: {username} {reason.lower()}.", username)
    update_online_users()
    print(f"{username} disconnected - {reason}")
    print_stats()

def save_history(sender, receiver, msg_type, message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(CHAT_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            timestamp, sender, receiver, msg_type, message
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
    global TOTAL_MESSAGES, BROADCAST_MESSAGES

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
    global TOTAL_MESSAGES, PRIVATE_MESSAGES
    
    valid, msg = validate_message(message)
    if not valid:
        clients[sender].send(f"ERROR: {msg}\n".encode())
        return
    
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
    save_history(sender, receiver, "PRIVATE", message)

def send_online_users(username):
    users = ",".join(clients.keys())
    text = f"ONLINE:{users}\n"
    clients[username].send(text.encode())

def update_online_users():
    users = ",".join(clients.keys())
    text = f"ONLINE:{users}\n"
    
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
    print("Active Sessions :", len(active_sessions))
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
    global TEST_START, TEST_END
    
    username = ""
    authenticated = False
    
    try:
        conn.send("LOGIN".encode())

        credentials = conn.recv(4096).decode().strip()

        username, password = credentials.split("|", 1)
        
        log_security_event("AUTH_ATTEMPT", username, "Authentication attempt")
        
        auth_success, auth_msg = authenticate_user(username, password)
        
        if not auth_success:
            conn.send(f"AUTH_FAILED: {auth_msg}\n".encode())
            log_security_event("AUTH_FAILED", username, auth_msg)
            conn.close()
            return
        
        login_allowed, login_msg = prevent_duplicate_login(username)
        if not login_allowed:
            conn.send(f"DUPLICATE_LOGIN: {login_msg}\n".encode())
            log_security_event("DUPLICATE_LOGIN_ATTEMPT", username, login_msg)
            conn.close()
            return
        
        authenticated = True
        
        with lock:
            clients[username] = conn
            active_sessions[username] = time.time()
            client_info[username] = {
                "ip": addr[0],
                "port": addr[1],
                "login_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "last_activity": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status": "Online"
            }
        
        log_security_event("SESSION_STARTED", username, 
            f"Connected from {addr[0]}:{addr[1]}")
        
        print(f"{username} connected from {addr[0]}:{addr[1]}")
        
        conn.send("\n=== Welcome to the Secure Chat Server ===\n".encode())
        conn.send("Commands:\n".encode())
        conn.send("  /list - Show online users\n".encode())
        conn.send("  /msg <user> <message> - Send private message\n".encode())
        conn.send("  /logout - Logout\n".encode())
        conn.send("==========================================\n".encode())
        
        history = get_last_messages(username)
        if history:
            conn.send("\nLast 5 messages:\n".encode())
            for msg in history:
                conn.send((msg + "\n").encode())
        
        broadcast(f"SYSTEM: {username} joined the chat.", username)
        update_online_users()
        print_stats()
        
        while True:
            try:
                conn.settimeout(30)
                message = conn.recv(MAX_MESSAGE_SIZE).decode()
                conn.settimeout(None)
                
                if not message:
                    break
                
                message = message.strip()
                
                update_activity(username)
                
                if message == "/logout":
                    logout_user(username, "User logged out")
                    break
                
                if message == "":
                    continue
                
                if message.startswith("/msg"):
                    parts = message.split(" ", 2)
                    if len(parts) < 3:
                        conn.send("Usage: /msg <username> <message>\n".encode())
                        continue
                    
                    receiver = parts[1]
                    text = parts[2]
                    
                    valid, msg = validate_username(receiver)
                    if not valid:
                        conn.send(f"ERROR: Invalid receiver username\n".encode())
                        continue
                    
                    private_message(username, receiver, text)
                    continue
                
                if message == "/list":
                    send_online_users(username)
                    continue

                if message.startswith("/") and \
                    not message.startswith("/msg") and \
                    message != "/list" and \
                    message != "/logout":

                        conn.send("ERROR: Unsupported command\n".encode())
                        continue

                if TEST_START is None:
                    TEST_START = datetime.now()
                
                valid, msg = validate_message(message)
                if not valid:
                    conn.send(f"ERROR: {msg}\n".encode())
                    continue
                
                text = f"{username}: {message}"

                try:
                    conn.send(f"You: {message}".encode())
                except:
                    pass

                broadcast(text, username)

                save_history(username, "ALL", "BROADCAST", message)
                
                TEST_END = datetime.now()
                print(text)
                
            except socket.timeout:
                if check_session_timeout(username):
                    break
                continue
            except Exception as e:
                print(f"Error in message loop: {e}")
                break
    
    except Exception as e:
        print(f"Error in client handler: {e}")
    
    finally:
        if authenticated:
            logout_user(username, "Disconnected")
        
        if len(clients) == 0:
            save_performance()
        
        try:
            conn.close()
        except:
            pass

def start_server():
    initialize_files()
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()
    
    print("=" * 50)
    print("SECURE TCP CHAT SERVER STARTED")
    print(f"Listening on {HOST}:{PORT}")
    print(f"Session timeout: {SESSION_TIMEOUT/60} minutes")
    print(f"Max login attempts: {MAX_LOGIN_ATTEMPTS}")
    print("=" * 50)
    
    log_security_event("SERVER_START", "SYSTEM", 
        f"Server started on {HOST}:{PORT}")
    
    while True:
        try:
            conn, addr = server.accept()
            thread = threading.Thread(
                target=handle_client,
                args=(conn, addr)
            )
            thread.daemon = True
            thread.start()
        except KeyboardInterrupt:
            print("\nShutting down server...")
            log_security_event("SERVER_SHUTDOWN", "SYSTEM", "Server shutting down")
            break
        except Exception as e:
            print(f"Server error: {e}")
            continue
    
    server.close()

if __name__ == "__main__":
    start_server()
