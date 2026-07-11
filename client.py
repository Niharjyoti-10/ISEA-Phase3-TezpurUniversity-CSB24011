import socket
import threading

HOST = "10.0.0.1"
PORT = 5000

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))

username = input("Enter Username: ")

client.send(username.encode())


def receive():
    while True:
        try:
            message = client.recv(1024).decode()
            print(message)
        except:
            print("Disconnected from server.")
            client.close()
            break


def write():
    while True:
        msg = input("")
        full_message = f"[{username}] {msg}"
        client.send(full_message.encode())


receive_thread = threading.Thread(target=receive)
receive_thread.daemon = True
receive_thread.start()

write()
