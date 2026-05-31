import socket

try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(3)
    s.connect(("naemini.local", 6379))
    print("TCP connection to naemini.local:6379 OK")

    s.send(b"*1\r\n$4\r\nPING\r\n")
    resp = s.recv(1024)
    print("Response:", repr(resp))

    s.close()
except Exception as e:
    print(type(e).__name__, e)
