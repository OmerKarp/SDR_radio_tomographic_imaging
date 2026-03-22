"""
Embedded Python Blocks:

Each time this file is saved, GRC will instantiate the first class it finds
to get ports and parameters of your block. The arguments to __init__  will
be the parameters. All of them are required to have default values!
"""

import pmt
import json
from gnuradio import gr
import numpy as np

class blk(gr.sync_block):
    def __init__(self, node_id=1):
        gr.sync_block.__init__(self,
            name="tx_controller",
            in_sig=None,
            out_sig=[np.complex64])

        # -----------------------------
        # PARAMETERS
        # -----------------------------
        self.node_id = int(node_id)

        # -----------------------------
        # MESSAGE INPUT (GRAY)
        # -----------------------------
        self.message_port_register_in(pmt.intern("in"))
        self.set_msg_handler(pmt.intern("in"), self.handle_msg)

        # -----------------------------
        # MESSAGE OUTPUT (GRAY)
        # -----------------------------
        self.message_port_register_out(pmt.intern("ctrl"))

        # Internal state
        self.tx_enable = False
        self.tx_node = None
        self.frame_id = None
    
    def work(self, input_items, output_items):
        out = output_items[0]

        value = 1.0 + 0j if self.tx_enable else 0.0 + 0j
        out[:] = value

        return len(out)

    # -----------------------------
    # MESSAGE HANDLER
    # -----------------------------
    def handle_msg(self, msg):
        try:
            # Extract payload from PDU
            payload = pmt.cdr(msg)
            payload_bytes = pmt.to_python(payload)

            # Decode JSON
            json_str = bytes(payload_bytes).decode('utf-8')
            data = json.loads(json_str)

            # Extract scheduler info
            self.tx_node = int(data.get("tx_node", -1))
            self.frame_id = int(data.get("frame_id", -1))

            # -----------------------------
            # CONTROL LOGIC
            # -----------------------------
            self.tx_enable = (self.tx_node == self.node_id)

            print(f"[NODE {self.node_id}] "
                  f"tx_node={self.tx_node}, "
                  f"frame_id={self.frame_id}, "
                  f"tx_enable={self.tx_enable}")

            # -----------------------------
            # OUTPUT CONTROL MESSAGE
            # -----------------------------
            ctrl_dict = {
                "tx_enable": self.tx_enable,
                "tx_node": self.tx_node,
                "frame_id": self.frame_id
            }
            ctrl_pmt = pmt.to_pmt(ctrl_dict)
            msg_out = pmt.cons(pmt.PMT_NIL, ctrl_pmt)

            self.message_port_pub(pmt.intern("ctrl"), msg_out)

        except Exception as e:
            print(f"[TX_CTRL ERROR] {e}")
