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
NODE_IDS = list(range(1, NODE_COUNT + 1))

SDR_IPS = ["192.168.20.35", "192.168.20.37"]

FRAME_TIME = 0.05
SERVER_PORT = 9000
SCHED_PORT = 9001

GRID_X, GRID_Y = 20, 20
LAMBDA = 0.1
ALPHA = 0.3  # smoothing

# -----------------------------
# NODE POSITIONS (edit as needed)
# -----------------------------
NODE_POS = {
    0: np.array([0, 0]),
    1: np.array([3, 0]),
}

# -----------------------------
# GLOBALS
# -----------------------------
rssi_matrix = np.zeros((NODE_COUNT, NODE_COUNT))
smoothed_matrix = np.zeros((NODE_COUNT, NODE_COUNT))
frame_data = {i: [] for i in range(NODE_COUNT)}

sched_tx_index = 0
current_tx_index = 0
last_frame_time = time.time()
frame_id = 0

# -----------------------------
# BUILD W MATRIX (RTI MODEL)
# -----------------------------
def build_W():
    num_links = NODE_COUNT * NODE_COUNT
    num_pixels = GRID_X * GRID_Y

    W = np.zeros((num_links, num_pixels))

    pixels = []
    for i in range(GRID_X):
        for j in range(GRID_Y):
            pixels.append(np.array([i, j]))

    link_idx = 0

    for tx in range(NODE_COUNT):
        for rx in range(NODE_COUNT):

            if tx == rx:
                link_idx += 1
                continue

            tx_pos = NODE_POS[tx]
            rx_pos = NODE_POS[rx]

            d = np.linalg.norm(tx_pos - rx_pos)

            for p_idx, p in enumerate(pixels):
                d1 = np.linalg.norm(p - tx_pos)
                d2 = np.linalg.norm(p - rx_pos)

                # Ellipse model
                if d1 + d2 <= d + 2:
                    W[link_idx, p_idx] = 1.0

            link_idx += 1

    return W

W = build_W()

# -----------------------------
# RECONSTRUCTION
# -----------------------------
def reconstruct_rti(matrix):
    y = matrix.flatten()

    x = np.linalg.inv(W.T @ W + LAMBDA * np.eye(W.shape[1])) @ W.T @ y

    return x.reshape(GRID_X, GRID_Y)

# -----------------------------
# PLOTTING
# -----------------------------
def plot_heatmap(grid):
    plt.clf()
    plt.imshow(grid, cmap='hot', interpolation='nearest')
    plt.colorbar(label='ΔRSSI')
    plt.title('RTI Heatmap')
    plt.pause(0.01)

# -----------------------------
# SCHEDULER
# -----------------------------
def tx_scheduler():
    global sched_tx_index, frame_id
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    while True:
        msg = {"tx_node": NODE_IDS[sched_tx_index], "frame_id": frame_id}

        print(f"[SCHED] TX node = {NODE_IDS[sched_tx_index]}")

        data = json.dumps(msg).encode()

        for ip in SDR_IPS:
            sock.sendto(data, (ip, SCHED_PORT))

        sched_tx_index = (sched_tx_index + 1) % NODE_COUNT
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

        # -----------------------------
        # RECEIVE DATA
        # -----------------------------
        try:
            data, addr = sock.recvfrom(1024)
            node_id, delta = struct.unpack("if", data)

            print(f"[RECV] from {addr} | Node {node_id} ΔRSSI={delta:.2f}")

            node_idx = node_id - 1
            frame_data[node_idx].append(delta)

        except BlockingIOError:
            pass

        # -----------------------------
        # FRAME UPDATE
        # -----------------------------
        if now - last_frame_time >= FRAME_TIME:

            for rx in range(NODE_COUNT):
                value = np.mean(frame_data[rx]) if frame_data[rx] else 0.0

                prev = smoothed_matrix[current_tx_index, rx]
                smoothed = ALPHA * value + (1 - ALPHA) * prev

                smoothed_matrix[current_tx_index, rx] = smoothed
                rssi_matrix[current_tx_index, rx] = smoothed

            # zero diagonal (no self-link)
            rssi_matrix[current_tx_index, current_tx_index] = 0.0

            print("Matrix:")
            print(rssi_matrix)
            print(f"[FRAME DONE] TX was {current_tx_index+1}")

            current_tx_index = (current_tx_index + 1) % NODE_COUNT

            frame_data = {i: [] for i in range(NODE_COUNT)}
            last_frame_time = now

            # -----------------------------
            # RTI RECONSTRUCTION
            # -----------------------------
            heatmap = reconstruct_rti(rssi_matrix)
            plot_heatmap(heatmap)