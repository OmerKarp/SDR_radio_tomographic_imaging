import socket, struct

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", 9000))

while True:
    data, addr = sock.recvfrom(1024)
    node_id, delta = struct.unpack("if", data)
    print(f"Node {node_id} ΔRSSI: {delta:.2f}")