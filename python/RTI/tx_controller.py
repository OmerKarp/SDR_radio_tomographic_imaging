#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 OmerKarp.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#


from gnuradio import gr
import pmt
import json
import numpy as np

class tx_controller(gr.sync_block):
    def __init__(self, node_id=1):
        gr.sync_block.__init__(
            self,
            name="tx_controller",
            in_sig=None,
            out_sig=[np.complex64]
        )

        # Parameters
        self.node_id = int(node_id)

        # Message ports
        self.message_port_register_in(pmt.intern("in"))
        self.set_msg_handler(pmt.intern("in"), self.handle_msg)

        self.message_port_register_out(pmt.intern("ctrl"))

        # State
        self.tx_enable = False
        self.tx_node = None
        self.frame_id = None

    def work(self, input_items, output_items):
        out = output_items[0]

        value = 1.0 + 0j if self.tx_enable else 0.0 + 0j
        out[:] = value

        return len(out)

    def handle_msg(self, msg):
        try:
            # Extract PDU
            payload = pmt.cdr(msg)
            payload_python = pmt.to_python(payload)

            # Convert bytes → JSON
            json_str = bytes(payload_python).decode('utf-8')
            data = json.loads(json_str)

            # Extract fields
            self.tx_node = int(data.get("tx_node", -1))
            self.frame_id = int(data.get("frame_id", -1))

            # Logic
            self.tx_enable = (self.tx_node == self.node_id)

            print(f"[NODE {self.node_id}] "
                  f"tx_node={self.tx_node}, "
                  f"frame_id={self.frame_id}, "
                  f"tx_enable={self.tx_enable}")

            # Send control message (PDU with dict)
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