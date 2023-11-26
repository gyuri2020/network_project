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


outputs = []

class ManyTCPConnectionTopology(Topo):
    def build(self):
        server = self.addHost('server', cls=Host, defaultRoute=None)
        switch = self.addSwitch('s1', cls=OVSKernelSwitch, failMode='standalone')

        self.addLink(server, switch, cls=TCLink, bw=1, delay='0.1ms', loss=0.3)

        for i in range(1, 201):
            host = self.addHost(f'h{i}', cls=Host, defaultRoute=None)
            self.addLink(host, switch, cls=TCLink, bw=1, delay='0.1ms', loss=0.3)




def ping_to_server(net, client, server):

    result = client.cmd(f"ping -c100 {server.IP()}")
    all_output = net._parsePingFull( result )
    outputs.append(list(all_output))


def main():
    topo = ManyTCPConnectionTopology()
    net = Mininet(topo=topo, autoSetMacs=True, build=False, ipBase="10.0.0.0/24")

    net.start()

    server = net.getNodeByName('server')
    server.setIP(intf="server-eth0", ip="10.0.0.1/24")
    #server.cmd(f'python3 server_tcp.py {server_ip} {server_port} &')

    #time.sleep(3)

    clients = []
    threads = []
    for i in range(1, 201):
        h = net.getNodeByName(f'h{i}')
        h.setIP(intf=f'h{i}-eth0', ip=f"10.0.0.{i+1}/24")
        clients.append(h) 


    for client in clients:
        t = threading.Thread(target=ping_to_server, args=(net, client, server))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()
    
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
    print(f"avg rttavg: {avg_rttavg}")
    print(f"avg rttmax: {avg_rttmax}")
    print(f"avg rttdev: {avg_rttdev}")

    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    main()
