import numpy as np
from rssi_sender import rssi_sender

# Create block
block = rssi_sender(node_id=1, server_ip="127.0.0.1", port=9000)

# Simulate 1 second of RSSI data at 1 kHz sample rate
for _ in range(50):  # 50 iterations ~ 1 s if batch is 20 ms
    fake_rssi = np.random.normal(-50, 1, 100)  # 100 samples per batch
    block.work([fake_rssi], None)