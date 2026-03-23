#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
from gnuradio import gr
import socket
import struct
import time
import pmt

class rssi_sender(gr.sync_block):
    def __init__(self, node_id=1, server_ip="192.168.1.100", port=9000, baseline_time=10):
        gr.sync_block.__init__(
            self,
            name="rssi_sender",
            in_sig=[np.float32],
            out_sig=None,
        )

        self.node_id = node_id
        self.server = (server_ip, port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.last_send = time.time()
        self.start_time = time.time()
        self.baseline_time = baseline_time

        self.baseline = None
        self.baseline_sum = 0.0
        self.baseline_count = 0

        self.is_tx = False
        self.smoothed_delta = None

        # CTRL input
        self.message_port_register_in(pmt.intern("ctrl"))
        self.set_msg_handler(pmt.intern("ctrl"), self.handle_ctrl)

    def work(self, input_items, output_items):
        rssi_samples = np.array(input_items[0], dtype=np.float32)
        now = time.time()

        # Ignore startup noise
        if now - self.start_time < 2:
            elapsed = now - self.start_time
            progress = min(elapsed / self.baseline_time, 1.0)

            filled = int(20 * progress)
            bar = "[" + "|" * filled + "." * (20 - filled) + "]"

            print(f"\rCalibrating {bar} {int(progress*100)}%")
            
            return len(rssi_samples)

        # -----------------------------
        # BASELINE PHASE
        # -----------------------------
        if self.baseline is None:
            self.baseline_sum += np.sum(rssi_samples)
            self.baseline_count += len(rssi_samples)

            elapsed = now - self.start_time
            progress = min(elapsed / self.baseline_time, 1.0)

            filled = int(20 * progress)
            bar = "[" + "|" * filled + "." * (20 - filled) + "]"

            print(f"\rCalibrating {bar} {int(progress*100)}%")

            if now - self.start_time >= self.baseline_time:
                self.baseline = self.baseline_sum / self.baseline_count
                print(f"[NODE {self.node_id}] Baseline RSSI: {self.baseline:.2f}")

            return len(rssi_samples)

        # -----------------------------
        # ΔRSSI COMPUTE
        # -----------------------------
        delta = rssi_samples[-1] - self.baseline

        # -----------------------------
        # EMA SMOOTHING
        # -----------------------------
        if self.smoothed_delta is None:
            self.smoothed_delta = delta

        self.smoothed_delta = 0.3 * delta + 0.7 * self.smoothed_delta
        delta = self.smoothed_delta

        print(f"[NODE {self.node_id}] TX={self.is_tx} ΔRSSI={delta:.2f}")

        # -----------------------------
        # SEND ONLY WHEN RECEIVING
        # -----------------------------
        if (not self.is_tx) and (now - self.last_send > 0.02):
            packet = struct.pack("if", self.node_id, float(delta))
            self.sock.sendto(packet, self.server)
            self.last_send = now

        return len(rssi_samples)

    def handle_ctrl(self, msg):
        try:
            data = pmt.to_python(pmt.cdr(msg))
            self.is_tx = bool(data.get("tx_enable", False))
        except Exception as e:
            print(f"[RSSI CTRL ERROR] {e}")