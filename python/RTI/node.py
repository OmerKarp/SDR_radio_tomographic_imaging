#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
from gnuradio import gr
import socket
import struct
import time
import threading
import json
import argparse

# -----------------------------
# RSSI SENDER BLOCK
# -----------------------------
class rssi_sender(gr.sync_block):
    def __init__(self, node_id=1, server_ip="192.168.1.100", server_port=9000, baseline_time=10):
        gr.sync_block.__init__(
            self,
            name="rssi_sender",
            in_sig=[np.float32],
            out_sig=None,
        )

        self.node_id = node_id
        self.server = (server_ip, server_port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.last_send = time.time()
        self.start_time = time.time()
        self.baseline_time = baseline_time

        self.baseline = None
        self.baseline_sum = 0.0
        self.baseline_count = 0

        self.is_tx = False  # controlled by scheduler

    def work(self, input_items, output_items):
        rssi_samples = np.array(input_items[0], dtype=np.float32)
        now = time.time()

        # -----------------------------
        # BASELINE PHASE
        # -----------------------------
        if self.baseline is None:
            self.baseline_sum += np.sum(rssi_samples)
            self.baseline_count += len(rssi_samples)
            if now - self.start_time >= self.baseline_time:
                self.baseline = self.baseline_sum / self.baseline_count
                print(f"Node {self.node_id} Baseline RSSI: {self.baseline:.2f}")
            return len(input_items[0])

        # -----------------------------
        # ΔRSSI COMPUTE
        # -----------------------------
        delta = np.mean(rssi_samples) - self.baseline
        print(f"[NODE {self.node_id}] TX={self.is_tx} ΔRSSI={delta:.2f}")

        # -----------------------------
        # SEND IF TX
        # -----------------------------
        if self.is_tx and (now - self.last_send > 0.02):
            packet = struct.pack("if", self.node_id, delta)
            self.sock.sendto(packet, self.server)
            self.last_send = now

        return len(input_items[0])

# -----------------------------
# SCHEDULER LISTENER
# -----------------------------
def tx_listener(block, listen_port=9001):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", listen_port))

    while True:
        data, _ = sock.recvfrom(1024)
        msg = json.loads(data.decode())
        block.is_tx = (msg.get("tx_node") == block.node_id)

# -----------------------------
# SIMULATION MODE
# -----------------------------
def run_simulation(block):
    print("Running in SIMULATION mode...")
    while True:
        fake_rssi = np.random.normal(-50 + block.node_id * 5, 1, 100)
        block.work([fake_rssi], None)
        time.sleep(0.01)

# -----------------------------
# REAL SDR MODE (HOOK)
# -----------------------------
def run_real():
    print("Running in REAL SDR mode...")
    while True:
        time.sleep(1)  # idle (GNU Radio drives the block)

# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--node_id", type=int, required=True)
    parser.add_argument("--server_ip", type=str, required=True)
    parser.add_argument("--mode", type=str, default="simulate", choices=["simulate", "real"])
    args = parser.parse_args()

    block = rssi_sender(
        node_id=args.node_id,
        server_ip=args.server_ip
    )

    # Start scheduler listener
    threading.Thread(target=tx_listener, args=(block,), daemon=True).start()

    if args.mode == "simulate":
        run_simulation(block)
    else:
        run_real()