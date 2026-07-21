import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox
import hashlib
import time

PORT = 5000
SESSION_TIMEOUT = 600

client = None
username = ""
authenticated = False
last_activity = time.time()
login_attempts = 0
max_attempts = 5
blocked_until = 0

root = tk.Tk()
root.title("Secure TCP Chat Client")
root.geometry("750x550")
root.resizable(False, False)

login_frame = tk.Frame(root)
login_frame.pack(fill="both", expand=True)

tk.Label(
    login_frame,
    text="Secure TCP Chat Client",
    font=("Arial", 18, "bold")
).pack(pady=20)

tk.Label(login_frame, text="Server IP").pack()
host_entry = tk.Entry(login_frame, width=30)
host_entry.insert(0, "10.0.0.1")
host_entry.pack(pady=5)

tk.Label(login_frame, text="Username").pack()
username_entry = tk.Entry(login_frame, width=30)
username_entry.pack(pady=5)

tk.Label(login_frame, text="Password").pack()
password_entry = tk.Entry(login_frame, width=30, show="*")
password_entry.pack(pady=5)

status_label = tk.Label(
    login_frame,
    text="Not Connected",
    fg="red"
)
status_label.pack(pady=5)

auth_status_label = tk.Label(
    login_frame,
    text="",
    fg="red"
)
auth_status_label.pack(pady=5)

chat_frame = tk.Frame(root)

left_frame = tk.Frame(chat_frame)
left_frame.pack(side="left", fill="both", expand=True)

right_frame = tk.Frame(chat_frame)
right_frame.pack(side="right", fill="y")

chat_box = scrolledtext.ScrolledText(
    left_frame,
    width=60,
    height=22,
    state="disabled"
)
chat_box.pack(padx=10, pady=10)

message_entry = tk.Entry(
    left_frame,
    width=50
)
message_entry.pack(
    side="left",
    padx=10,
    pady=5
)

send_btn = tk.Button(
    left_frame,
    text="Send"
)
send_btn.pack(
    side="left",
    padx=5
)

logout_btn = tk.Button(
    right_frame,
    text="Logout",
    width=18
)
logout_btn.pack(pady=10)

tk.Label(
    right_frame,
    text="Online Users"
).pack()

online_list = tk.Listbox(
    right_frame,
    width=20,
    height=20
)
online_list.pack(padx=10)

session_label = tk.Label(
    right_frame,
    text="",
    fg="blue",
    font=("Arial", 8)
)
session_label.pack(pady=5)

def update_session_timer():
    if authenticated:
        elapsed = int(time.time() - last_activity)
        remaining = SESSION_TIMEOUT - elapsed
        if remaining > 0:
            mins = remaining // 60
            secs = remaining % 60
            session_label.config(text=f"Session: {mins:02d}:{secs:02d}")
            root.after(1000, update_session_timer)
        else:
            session_label.config(text="Session Expired")
            messagebox.showwarning("Session Timeout", "Session expired. Please login again.")
            logout()

def receive():
    global authenticated, last_activity

    while True:
        try:
            data = client.recv(4096).decode()

            if not data:
                break

            # Split multiple messages received together
            messages = data.split("\n")

            for message in messages:

                message = message.strip()

                if not message:
                    continue

                if message.startswith("ONLINE:"):
                    users = message.replace("ONLINE:", "").split(",")

                    online_list.delete(0, tk.END)

                    for user in users:
                        user = user.strip()
                        if user:
                            online_list.insert(tk.END, user)

                elif message.startswith("AUTH_FAILED:"):
                    auth_msg = message.replace("AUTH_FAILED:", "")
                    auth_status_label.config(text=auth_msg, fg="red")
                    messagebox.showerror("Authentication Failed", auth_msg)

                elif message.startswith("DUPLICATE_LOGIN:"):
                    dup_msg = message.replace("DUPLICATE_LOGIN:", "")
                    auth_status_label.config(text=dup_msg, fg="red")
                    messagebox.showerror("Duplicate Login", dup_msg)

                elif message.startswith("LOGOUT:"):
                    messagebox.showinfo("Logged Out", "You have been logged out.")
                    logout()
                    return

                else:
                    last_activity = time.time()

                    chat_box.config(state="normal")
                    chat_box.insert(tk.END, message + "\n")
                    chat_box.see(tk.END)
                    chat_box.config(state="disabled")

        except socket.timeout:
            continue

        except Exception as e:
            print("Receive Error:", e)
            break

    try:
        client.close()
    except:
        pass
def connect_server():
    global client, username, authenticated, last_activity, login_attempts, blocked_until
    
    host = host_entry.get().strip()
    username = username_entry.get().strip()
    password = password_entry.get().strip()
    
    if host == "" or username == "" or password == "":
        messagebox.showerror("Error", "Fill all fields.")
        return
    
    if blocked_until > time.time():
        remaining = int((blocked_until - time.time()) / 60)
        messagebox.showerror("Account Blocked", f"Account blocked. Try again in {remaining} minutes.")
        return
    
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.settimeout(30)
    
    try:
        client.connect((host, PORT))
    except:
        messagebox.showerror("Error", "Unable to connect to server.")
        return
    
    try:
        
        server_msg = client.recv(1024).decode()

        if server_msg != "LOGIN":
            raise Exception("Unexpected server response")

        auth_status_label.config(text="Authenticating...", fg="blue")

        client.send(f"{username}|{password}".encode())

        response = client.recv(4096).decode()
        
        if response.startswith("AUTH_FAILED:"):
            auth_msg = response.replace("AUTH_FAILED:", "")
            auth_status_label.config(text=auth_msg, fg="red")
            messagebox.showerror("Authentication Failed", auth_msg)
            login_attempts += 1
            
            if login_attempts >= max_attempts:
                blocked_until = time.time() + 300
                messagebox.showwarning("Account Blocked", 
                    "Too many failed attempts. Account blocked for 5 minutes.")
            
            client.close()
            return
        
        if response.startswith("DUPLICATE_LOGIN:"):
            dup_msg = response.replace("DUPLICATE_LOGIN:", "")
            auth_status_label.config(text=dup_msg, fg="red")
            messagebox.showerror("Duplicate Login", dup_msg)
            client.close()
            return
        
        authenticated = True
        last_activity = time.time()
        login_attempts = 0
        
        status_label.config(text="Connected", fg="green")
        auth_status_label.config(text="Authenticated", fg="green")
        
        login_frame.pack_forget()
        chat_frame.pack(fill="both", expand=True)
               
        message_entry.focus_set()
        
        update_session_timer()
        
        threading.Thread(target=receive, daemon=True).start()
        
    except Exception as e:
        messagebox.showerror("Error", f"Connection error: {str(e)}")
        client.close()

def send_message():
    global client, last_activity
    
    if client is None or not authenticated:
        messagebox.showerror("Error", "Not connected or authenticated.")
        return
    
    message = message_entry.get().strip()
    
    if not message:
        return
    
    if len(message) > 4096:
        messagebox.showerror("Error", "Message too long (max 4096 characters)")
        return
    
    try:
        client.send(message.encode())
        last_activity = time.time()
        message_entry.delete(0, tk.END)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to send: {str(e)}")

def logout():
    global client, authenticated
    
    if client:
        try:
            client.send("/logout".encode())
        except:
            pass
        try:
            client.close()
        except:
            pass
    
    authenticated = False
    client = None
    
    chat_frame.pack_forget()
    login_frame.pack(fill="both", expand=True)
    status_label.config(text="Disconnected", fg="red")
    auth_status_label.config(text="", fg="red")
    session_label.config(text="")

def on_close():
    logout()
    root.destroy()

send_btn.config(command=send_message)
logout_btn.config(command=logout)

connect_btn = tk.Button(
    login_frame,
    text="Connect",
    width=20,
    command=connect_server
)
connect_btn.pack(pady=10)

message_entry.bind(
    "<Return>",
    lambda event: (send_message(), "break")[1]
)

root.protocol("WM_DELETE_WINDOW", on_close)

root.mainloop()
