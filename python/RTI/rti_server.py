#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import struct
import numpy as np
import matplotlib.pyplot as plt
import time

# -------------------------------
# CONFIGURATION
# -------------------------------
NODE_COUNT = 4       # total SDR nodes
FRAME_TIME = 0.05    # seconds per Tx frame
PORT = 9000

# 2D area for visualization (arbitrary grid)
GRID_X = 20
GRID_Y = 20

# RTI reconstruction regularization
LAMBDA = 0.1

# -------------------------------
# INITIALIZATION
# -------------------------------
# Full ΔRSSI matrix: rows=Tx, cols=Rx
rssi_matrix = np.zeros((NODE_COUNT, NODE_COUNT))

# Keep track of which node is currently Tx
tx_index = 0
last_frame_time = time.time()

# Store packets per frame for averaging
frame_data = {i: [] for i in range(NODE_COUNT)}

# UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", PORT))
sock.setblocking(False)

print(f"RTI server running on UDP port {PORT}...")

# -------------------------------
# HELPER FUNCTIONS
# -------------------------------
def reconstruct_rti(matrix):
    """
    Simple Tikhonov regularization RTI reconstruction
    """
    y = matrix.flatten()
    W = np.eye(len(y))
    heatmap_vector = np.linalg.inv(W.T @ W + LAMBDA * np.eye(len(y))) @ W.T @ y
    return heatmap_vector.reshape(GRID_X, GRID_Y)

def plot_heatmap(grid):
    plt.clf()
    plt.imshow(grid, cmap='hot', interpolation='nearest')
    plt.colorbar(label='ΔRSSI')
    plt.title('RTI Heatmap')
    plt.pause(0.01)

# -------------------------------
# MAIN LOOP
# -------------------------------
plt.ion()
while True:
    now = time.time()

    # Rotate Tx node every FRAME_TIME
    if now - last_frame_time >= FRAME_TIME:
        # Average collected deltas for this frame
        for rx in range(NODE_COUNT):
            if frame_data[rx]:
                avg_delta = np.mean(frame_data[rx])
            else:
                avg_delta = 0.0
            rssi_matrix[tx_index, rx] = avg_delta

        rssi_matrix[tx_index, tx_index] = 0.0  # Tx->Tx = 0
        frame_data = {i: [] for i in range(NODE_COUNT)}  # reset for next frame

        # Move to next Tx
        tx_index = (tx_index + 1) % NODE_COUNT
        last_frame_time = now

        # Reconstruct and plot
        heatmap = reconstruct_rti(rssi_matrix)
        plot_heatmap(heatmap)

    # Non-blocking receive
    try:
        data, addr = sock.recvfrom(1024)
        node_id, delta = struct.unpack("if", data)
        node_idx = node_id - 1

        # Only collect deltas for the current Tx node
        if node_idx != tx_index:
            frame_data[node_idx].append(delta)

        print(f"Node {node_id} ΔRSSI: {delta:.2f}")

    except BlockingIOError:
        # No data received
        pass