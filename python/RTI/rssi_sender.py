import numpy as np
from gnuradio import gr
import socket
import struct
import time
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

        # Baseline computation
        self.baseline = None
        self.baseline_sum = 0.0
        self.baseline_count = 0

        # TX control: by default assume always Tx
        self.is_tx = True  # This will be controlled externally

    def work(self, input_items, output_items):
        rssi_samples = np.array(input_items[0], dtype=np.float32)
        now = time.time()

        # --- Baseline calculation ---
        if self.baseline is None:
            self.baseline_sum += np.sum(rssi_samples)
            self.baseline_count += len(rssi_samples)
            if now - self.start_time >= self.baseline_time:
                self.baseline = self.baseline_sum / self.baseline_count
                print(f"Node {self.node_id} Baseline RSSI:", self.baseline)
            return len(input_items[0])

        # --- Compute average delta ---
        delta = np.mean(rssi_samples) - self.baseline
        # print(f"Node {self.node_id} ΔRSSI:", delta)

        # --- Send only if this node is Tx ---
        if self.is_tx and (now - self.last_send > 0.02):
            packet = struct.pack("if", self.node_id, delta)
            self.sock.sendto(packet, self.server)
            self.last_send = now

        return len(input_items[0])