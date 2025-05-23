# Client testing time :D

import socket

HEADER = 64
PORT = 50512
FORMAT = "utf-8"
DISCONNECT_MESSAGE = "DISCONNECT"
SERVER = "10.190.207.221" #socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(ADDR)

def send(msg):
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b" " * (HEADER - len(send_length))
    client.send(send_length)
    client.send(message)

while True:
    print("Message to send:")
    msg = input()
    if msg == "stop":
        send(DISCONNECT_MESSAGE)
        break
    else:
        send(msg)

print("Stopped")


