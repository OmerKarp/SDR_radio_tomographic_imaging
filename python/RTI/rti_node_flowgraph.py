#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: rti_node_flowgraph
# Author: OmerKarp
# Copyright: OmerKarp
# GNU Radio version: 3.10.9.2

from gnuradio import analog
from gnuradio import blocks
from gnuradio import gr
from gnuradio.filter import firdes
from gnuradio.fft import window
import sys
import signal
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
from gnuradio import network
import rti_node_flowgraph_epy_block_0 as epy_block_0  # embedded python block




class rti_node_flowgraph(gr.top_block):

    def __init__(self):
        gr.top_block.__init__(self, "rti_node_flowgraph", catch_exceptions=True)

        ##################################################
        # Variables
        ##################################################
        self.server_port = server_port = 9000
        self.server_ip = server_ip = "127.0.0.1"
        self.scheduler_port = scheduler_port = "9001"
        self.samp_rate = samp_rate = 1e6
        self.node_id = node_id = 1
        self.freq = freq = 915e6
        self.Tx_gain = Tx_gain = 45
        self.Rx_gain = Rx_gain = 35

        ##################################################
        # Blocks
        ##################################################

        self.network_socket_pdu_0 = network.socket_pdu('UDP_SERVER', '0.0.0.0', scheduler_port, 10000, False)
        self.epy_block_0 = epy_block_0.blk(node_id=node_id)
        self.blocks_null_sink_0 = blocks.null_sink(gr.sizeof_gr_complex*1)
        self.blocks_multiply_xx_0 = blocks.multiply_vcc(1)
        self.analog_sig_source_x_0 = analog.sig_source_c(samp_rate, analog.GR_COS_WAVE, 10000, 0.5, 0, 0)


        ##################################################
        # Connections
        ##################################################
        self.msg_connect((self.network_socket_pdu_0, 'pdus'), (self.epy_block_0, 'in'))
        self.connect((self.analog_sig_source_x_0, 0), (self.blocks_multiply_xx_0, 0))
        self.connect((self.blocks_multiply_xx_0, 0), (self.blocks_null_sink_0, 0))
        self.connect((self.epy_block_0, 0), (self.blocks_multiply_xx_0, 1))


    def get_server_port(self):
        return self.server_port

    def set_server_port(self, server_port):
        self.server_port = server_port

    def get_server_ip(self):
        return self.server_ip

    def set_server_ip(self, server_ip):
        self.server_ip = server_ip

    def get_scheduler_port(self):
        return self.scheduler_port

    def set_scheduler_port(self, scheduler_port):
        self.scheduler_port = scheduler_port

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.analog_sig_source_x_0.set_sampling_freq(self.samp_rate)

    def get_node_id(self):
        return self.node_id

    def set_node_id(self, node_id):
        self.node_id = node_id
        self.epy_block_0.node_id = self.node_id

    def get_freq(self):
        return self.freq

    def set_freq(self, freq):
        self.freq = freq

    def get_Tx_gain(self):
        return self.Tx_gain

    def set_Tx_gain(self, Tx_gain):
        self.Tx_gain = Tx_gain

    def get_Rx_gain(self):
        return self.Rx_gain

    def set_Rx_gain(self, Rx_gain):
        self.Rx_gain = Rx_gain




def main(top_block_cls=rti_node_flowgraph, options=None):
    tb = top_block_cls()

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        sys.exit(0)

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    tb.start()

    try:
        input('Press Enter to quit: ')
    except EOFError:
        pass
    tb.stop()
    tb.wait()


if __name__ == '__main__':
    main()
