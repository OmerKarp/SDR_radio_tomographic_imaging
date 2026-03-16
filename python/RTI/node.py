import socket
import threading

from rti_node_flowgraph import rti_node_flowgraph

CMD_PORT = 9001


class NodeController:

    def __init__(self, tb):

        self.tb = tb

        # UDP socket for commands from server
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("", CMD_PORT))

        thread = threading.Thread(target=self.listen)
        thread.daemon = True
        thread.start()

    def listen(self):

        while True:

            data, _ = self.sock.recvfrom(1024)

            cmd = data.decode().strip()

            if cmd == "TX_ON":
                print("TX ON")
                self.tb.set_tx_enable(1)

            elif cmd == "TX_OFF":
                print("TX OFF")
                self.tb.set_tx_enable(0)


if __name__ == "__main__":

    tb = rti_node_flowgraph()

    controller = NodeController(tb)

    tb.start()

    print("Node running")

    try:
        input("Press Enter to stop\n")
    except KeyboardInterrupt:
        pass

    tb.stop()
    tb.wait()