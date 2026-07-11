import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox

PORT = 5000

client = None

root = tk.Tk()
root.title("TCP Chat Client")
root.geometry("750x500")
root.resizable(False, False)

login_frame = tk.Frame(root)
login_frame.pack(fill="both", expand=True)

tk.Label(
    login_frame,
    text="TCP Chat Client",
    font=("Arial", 18, "bold")
).pack(pady=20)

tk.Label(login_frame, text="Server IP").pack()

host_entry = tk.Entry(login_frame, width=30)
host_entry.insert(0, "10.0.0.1")
host_entry.pack(pady=5)

tk.Label(login_frame, text="Username").pack()

username_entry = tk.Entry(login_frame, width=30)
username_entry.pack(pady=5)

status_label = tk.Label(
    login_frame,
    text="Not Connected",
    fg="red"
)
status_label.pack(pady=10)


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

disconnect_btn = tk.Button(
    right_frame,
    text="Disconnect",
    width=18
)
disconnect_btn.pack(pady=10)

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

def receive():

    while True:

        try:

            message = client.recv(4096).decode()

            if not message:
                break

            if message.startswith("ONLINE:"):

                users = message.replace(
                    "ONLINE:",
                    ""
                ).split(",")

                online_list.delete(0, tk.END)

                for user in users:

                    if user.strip():
                        online_list.insert(
                            tk.END,
                            user.strip()
                        )

            else:

                chat_box.config(state="normal")

                chat_box.insert(
                    tk.END,
                    message + "\n"
                )

                chat_box.see(tk.END)

                chat_box.config(state="disabled")

        except:
            break

    try:
        client.close()
    except:
        pass


def connect_server():

    global client

    host = host_entry.get().strip()

    username = username_entry.get().strip()

    if host == "" or username == "":

        messagebox.showerror(
            "Error",
            "Fill all fields."
        )

        return

    client = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    try:

        client.connect((host, PORT))

    except:

        messagebox.showerror(
            "Error",
            "Unable to connect."
        )

        return

    client.recv(1024).decode()

    client.send(username.encode())

    welcome = client.recv(4096).decode()

    chat_box.config(state="normal")
    chat_box.insert(tk.END, welcome + "\n")
    chat_box.config(state="disabled")

    status_label.config(
        text="Connected",
        fg="green"
    )

    login_frame.pack_forget()

    chat_frame.pack(
        fill="both",
        expand=True
    )

    message_entry.focus_set()

    threading.Thread(
        target=receive,
        daemon=True
    ).start()


def send_message():
    global client

    print("Send button clicked")

    if client is None:
        print("Client is None")
        return

    message = message_entry.get().strip()
    print("Message =", repr(message))

    if not message:
        print("Empty message")
        return

    try:
        client.send(message.encode())
        print("Message sent")
        message_entry.delete(0, tk.END)
    except Exception as e:
        print("ERROR:", e)
        messagebox.showerror("Error", str(e))


def disconnect():

    global client

    try:
        client.send("/quit".encode())
        client.close()

    except:
        pass

    root.destroy()



def on_close():

    disconnect()


send_btn.config(command=send_message)

disconnect_btn.config(command=disconnect)

connect_btn = tk.Button(
    login_frame,
    text="Connect",
    width=20,
    command=connect_server
)

connect_btn.pack(pady=15)


message_entry.bind(
    "<Return>",
    lambda event: (send_message(), "break")[1]
)


root.protocol(
    "WM_DELETE_WINDOW",
    on_close
)

root.mainloop()
