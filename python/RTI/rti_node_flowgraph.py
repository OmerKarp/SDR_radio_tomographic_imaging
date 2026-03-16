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

from gnuradio import RTI
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
from gnuradio import uhd
import time




class rti_node_flowgraph(gr.top_block):

    def __init__(self):
        gr.top_block.__init__(self, "rti_node_flowgraph", catch_exceptions=True)

        ##################################################
        # Variables
        ##################################################
        self.tx_enable = tx_enable = 0
        self.server_port = server_port = 9000
        self.server_ip = server_ip = "127.0.0.1"
        self.samp_rate = samp_rate = 1e6
        self.node_id = node_id = 1
        self.freq = freq = 915e6
        self.Tx_gain = Tx_gain = 45
        self.Rx_gain = Rx_gain = 35

        ##################################################
        # Blocks
        ##################################################

        self.uhd_usrp_source_0 = uhd.usrp_source(
            ",".join(("", '')),
            uhd.stream_args(
                cpu_format="fc32",
                args='',
                channels=list(range(0,1)),
            ),
        )
        self.uhd_usrp_source_0.set_samp_rate(samp_rate)
        self.uhd_usrp_source_0.set_time_unknown_pps(uhd.time_spec(0))

        self.uhd_usrp_source_0.set_center_freq(freq, 0)
        self.uhd_usrp_source_0.set_antenna("RX2", 0)
        self.uhd_usrp_source_0.set_gain(Rx_gain, 0)
        self.uhd_usrp_sink_0 = uhd.usrp_sink(
            ",".join(("", '')),
            uhd.stream_args(
                cpu_format="fc32",
                args='',
                channels=list(range(0,1)),
            ),
            "",
        )
        self.uhd_usrp_sink_0.set_samp_rate(samp_rate)
        self.uhd_usrp_sink_0.set_time_unknown_pps(uhd.time_spec(0))

        self.uhd_usrp_sink_0.set_center_freq(freq, 0)
        self.uhd_usrp_sink_0.set_antenna("TX/RX", 0)
        self.uhd_usrp_sink_0.set_gain(Tx_gain, 0)
        self.blocks_nlog10_ff_0 = blocks.nlog10_ff(1, 1, 0)
        self.blocks_multiply_const_vxx_0_0 = blocks.multiply_const_ff(10)
        self.blocks_multiply_const_vxx_0 = blocks.multiply_const_cc(tx_enable)
        self.blocks_moving_average_xx_0 = blocks.moving_average_ff(4096, (1/4096), 4000, 1)
        self.blocks_complex_to_mag_squared_0 = blocks.complex_to_mag_squared(1)
        self.analog_sig_source_x_0 = analog.sig_source_c(samp_rate, analog.GR_COS_WAVE, 10000, 0.5, 0, 0)
        self.RTI_rssi_sender_0 = RTI.rssi_sender(node_id, server_ip, server_port)


        ##################################################
        # Connections
        ##################################################
        self.connect((self.analog_sig_source_x_0, 0), (self.blocks_multiply_const_vxx_0, 0))
        self.connect((self.blocks_complex_to_mag_squared_0, 0), (self.blocks_moving_average_xx_0, 0))
        self.connect((self.blocks_moving_average_xx_0, 0), (self.blocks_nlog10_ff_0, 0))
        self.connect((self.blocks_multiply_const_vxx_0, 0), (self.uhd_usrp_sink_0, 0))
        self.connect((self.blocks_multiply_const_vxx_0_0, 0), (self.RTI_rssi_sender_0, 0))
        self.connect((self.blocks_nlog10_ff_0, 0), (self.blocks_multiply_const_vxx_0_0, 0))
        self.connect((self.uhd_usrp_source_0, 0), (self.blocks_complex_to_mag_squared_0, 0))


    def get_tx_enable(self):
        return self.tx_enable

    def set_tx_enable(self, tx_enable):
        self.tx_enable = tx_enable
        self.blocks_multiply_const_vxx_0.set_k(self.tx_enable)

    def get_server_port(self):
        return self.server_port

    def set_server_port(self, server_port):
        self.server_port = server_port

    def get_server_ip(self):
        return self.server_ip

    def set_server_ip(self, server_ip):
        self.server_ip = server_ip

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.analog_sig_source_x_0.set_sampling_freq(self.samp_rate)
        self.uhd_usrp_sink_0.set_samp_rate(self.samp_rate)
        self.uhd_usrp_source_0.set_samp_rate(self.samp_rate)

    def get_node_id(self):
        return self.node_id

    def set_node_id(self, node_id):
        self.node_id = node_id

    def get_freq(self):
        return self.freq

    def set_freq(self, freq):
        self.freq = freq
        self.uhd_usrp_sink_0.set_center_freq(self.freq, 0)
        self.uhd_usrp_source_0.set_center_freq(self.freq, 0)

    def get_Tx_gain(self):
        return self.Tx_gain

    def set_Tx_gain(self, Tx_gain):
        self.Tx_gain = Tx_gain
        self.uhd_usrp_sink_0.set_gain(self.Tx_gain, 0)

    def get_Rx_gain(self):
        return self.Rx_gain

    def set_Rx_gain(self, Rx_gain):
        self.Rx_gain = Rx_gain
        self.uhd_usrp_source_0.set_gain(self.Rx_gain, 0)




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
