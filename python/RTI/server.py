#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import struct
import json
import numpy as np
import matplotlib.pyplot as plt
import time
import threading

# -----------------------------
# CONFIGURATION
# -----------------------------
NODE_COUNT = 2
NODE_IDS = [1,2]
SDR_IPS = ["192.168.20.16", "192.168.20.25"]  # Node IPs
FRAME_TIME = 0.05  # Tx rotation
SERVER_PORT = 9000
SCHED_PORT = 9001

GRID_X, GRID_Y = 20, 20
LAMBDA = 0.1

# -----------------------------
# GLOBALS
# -----------------------------
rssi_matrix = np.zeros((NODE_COUNT, NODE_COUNT))
frame_data = {i: [] for i in range(NODE_COUNT)}
tx_index = 0
last_frame_time = time.time()
frame_id = 0

# -----------------------------
# RECONSTRUCTION
# -----------------------------
def reconstruct_rti(matrix):
    y = matrix.flatten()
    W = np.eye(len(y))
    heatmap_vector = np.linalg.inv(W.T @ W + LAMBDA*np.eye(len(y))) @ W.T @ y
    return heatmap_vector.reshape(GRID_X, GRID_Y)

def plot_heatmap(grid):
    plt.clf()
    plt.imshow(grid, cmap='hot', interpolation='nearest')
    plt.colorbar(label='ΔRSSI')
    plt.title('RTI Heatmap')
    plt.pause(0.01)

# -----------------------------
# SCHEDULER THREAD
# -----------------------------
def tx_scheduler():
    global tx_index, frame_id
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    while True:
        msg = {"tx_node": NODE_IDS[tx_index], "frame_id": frame_id}
        data = json.dumps(msg).encode()
        for ip in SDR_IPS:
            sock.sendto(data, (ip, SCHED_PORT))
        # Next node
        tx_index = (tx_index + 1) % NODE_COUNT
        frame_id += 1
        time.sleep(FRAME_TIME)

# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", SERVER_PORT))
    sock.setblocking(False)

    threading.Thread(target=tx_scheduler, daemon=True).start()
    plt.ion()
    print("Server running...")

    while True:
        now = time.time()
        try:
            data, addr = sock.recvfrom(1024)
            node_id, delta = struct.unpack("if", data)
            node_idx = node_id - 1
            frame_data[node_idx].append(delta)
        except BlockingIOError:
            pass

        # Rotate frames
        if now - last_frame_time >= FRAME_TIME:
            for rx in range(NODE_COUNT):
                rssi_matrix[tx_index, rx] = np.mean(frame_data[rx]) if frame_data[rx] else 0.0
            rssi_matrix[tx_index, tx_index] = 0.0
            frame_data = {i: [] for i in range(NODE_COUNT)}
            last_frame_time = now
            # heatmap = reconstruct_rti(rssi_matrix)
            plot_heatmap(rssi_matrix)