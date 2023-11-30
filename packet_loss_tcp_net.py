from mininet.net import Mininet
from mininet.topo import Topo
from mininet.node import OVSKernelSwitch    
from mininet.cli import CLI
from mininet.node import Host
from mininet.log import setLogLevel, info
from mininet.link import TCLink
import socket
import time
import threading
import re



outputs = []
link_util_dict = dict()


def _parse_config(output):
    interface_data = re.findall(
        r"eth0.*?RX packets (\d+).*?bytes (\d+).*?TX packets (\d+).*?bytes (\d+)",
        output,
        re.DOTALL,
    )

    rx_packets, rx_bytes, tx_packets, tx_bytes = interface_data[0]
    dict = {
        "rx_packets": rx_packets,
        "rx_bytes": rx_bytes,
        "tx_packets": tx_packets,
        "tx_bytes": tx_bytes,
    }
    return dict
        


def ifconfigTest(node, elapsed):

        config_str = node.cmd( 'ifconfig' )
        packet_dict = _parse_config(config_str)
        rx_bytes = int(packet_dict["rx_bytes"])
        tx_bytes = int(packet_dict["tx_bytes"])
        total_bytes = rx_bytes + tx_bytes
        bw = 1 #1Mbps
        link_util = total_bytes * 8 / (bw * 1000000 * elapsed)
        link_util_dict[node.name] = link_util



class ManyPacketLossTopology(Topo):
    def build(self):
        server = self.addHost('server', cls=Host, defaultRoute=None)
        switch = self.addSwitch('s1', cls=OVSKernelSwitch, failMode='standalone')

        self.addLink(server, switch, cls=TCLink, bw=1, delay='0.1ms', loss=10)

        for i in range(1, 11):
            host = self.addHost(f'h{i}', cls=Host, defaultRoute=None)
            self.addLink(host, switch, cls=TCLink, bw=1, delay='0.1ms', loss=10)




def ping_to_server(net, client, server):

    start = time.time()
    result = client.cmd(f"ping -c100 {server.IP()}")
    all_output = net._parsePingFull( result )
    outputs.append(list(all_output))
    end = time.time()
    elapsed = end - start
    ifconfigTest(client, elapsed)


def main():
    topo = ManyPacketLossTopology()
    net = Mininet(topo=topo, autoSetMacs=True, build=False, ipBase="10.0.0.0/24")

    net.start()

    server = net.getNodeByName('server')
    server.setIP(intf="server-eth0", ip="10.0.0.1/24")
    #server.cmd(f'python3 server_tcp.py {server_ip} {server_port} &')

    #time.sleep(3)

    clients = []
    threads = []
    for i in range(1, 11):
        h = net.getNodeByName(f'h{i}')
        h.setIP(intf=f'h{i}-eth0', ip=f"10.0.0.{i+1}/24")
        clients.append(h) 


    for client in clients:
        t = threading.Thread(target=ping_to_server, args=(net, client, server))
        threads.append(t)
        t.start()

    start = time.time()
    for t in threads:
        t.join()
    end = time.time()
    elapsed = end - start
    ifconfigTest(server, elapsed)
    
    sent, received, rttmin, rttavg, rttmax, rttdev = [], [], [], [], [], []
    for output in outputs:
        sent.append(output[0])
        received.append(output[1])
        rttmin.append(output[2])
        rttavg.append(output[3])
        rttmax.append(output[4])
        rttdev.append(output[5])

    total_sent = sum(sent)
    total_received = sum(received)
    avg_rttmin = sum(rttmin) / len(rttmin)
    avg_rttavg = sum(rttavg) / len(rttavg)
    avg_rttmax = sum(rttmax) / len(rttmax)
    avg_rttdev = sum(rttdev) / len(rttdev)
    print(f"total sent: {total_sent}")
    print(f"total received: {total_received}")
    print(f"avg rttmin: {avg_rttmin}")
    print(f"avg rttavg: {avg_rttavg}") #latency
    print(f"avg rttmax: {avg_rttmax}")
    print(f"avg rttdev: {avg_rttdev}")

    client_link_util = []
    for name, link_util in link_util_dict.items():
        if name != "server":
            client_link_util.append(link_util)
    avg_client_link_util = sum(client_link_util) / len(client_link_util)
    std_client_link_util = sum([(x - avg_client_link_util) ** 2 for x in client_link_util]) / len(client_link_util)
    print(f"server link_util: {link_util_dict['server']}")
    print(f"avg client link_util: {avg_client_link_util}") #link_util
    print(f"std client link_util: {std_client_link_util}") #fairness
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    main()
