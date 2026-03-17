#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import time
import json

# -------------------------------
# CONFIGURATION
# -------------------------------
NODE_COUNT = 2  # number of SDR nodes (change to 4 later if needed)

# IPs of the machines running the SDRs
SDR_IPS = [
    "192.168.1.101",  # SDR node 1
    "192.168.1.102",  # SDR node 2
]

PORT = 9001          # port SDRs listen on
FRAME_TIME = 0.05    # 50 ms per Tx slot

# -------------------------------
# INITIALIZATION
# -------------------------------
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

tx_index = 0
frame_id = 0

print("Tx scheduler running...")

# -------------------------------
# MAIN LOOP
# -------------------------------
while True:
    # Create message
    msg = {
        "tx_node": tx_index + 1,  # node IDs are 1-based
        "frame_id": frame_id
    }

    data = json.dumps(msg).encode()

    # Broadcast to all SDR nodes
    for ip in SDR_IPS:
        sock.sendto(data, (ip, PORT))

    print(f"Frame {frame_id}: TX node = {tx_index + 1}")

    # Move to next node
    tx_index = (tx_index + 1) % NODE_COUNT
    frame_id += 1

    time.sleep(FRAME_TIME)