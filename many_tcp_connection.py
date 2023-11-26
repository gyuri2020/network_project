from mininet.net import Mininet
from mininet.topo import Topo
from mininet.node import OVSKernelSwitch
from mininet.cli import CLI
from mininet.node import Host
from mininet.log import setLogLevel, info
from mininet.link import TCLink
import threading

class ManyTCPConnectionTopology(Topo):
    def build(self):
        server = self.addHost('server', cls=Host, defaultRoute=None)
        switch = self.addSwitch('s1', cls=OVSKernelSwitch, failMode='standalone')

        self.addLink(server, switch, cls=TCLink, bw=10000000, delay='0.1ms')

def iperf_client(host, server_ip, port):
    host.cmd(f"iperf -c {server_ip} -p {port} -t 10 &")

def main():
    topo = ManyTCPConnectionTopology()
    net = Mininet(topo=topo, autoSetMacs=True, build=False, ipBase="10.0.0.0/24")

    net.start()

    server = net.getNodeByName('server')

    server.setIP(intf="server-eth0", ip="10.0.0.1/24")

    server_ip = "10.0.0.1"
    server_port = 5001

    for i in range(64):
        h = net.addHost(f'h{i+1}', cls=Host, defaultRoute=None)
        net.addLink(h, net.get('s1'), cls=TCLink, bw=10000000, delay='0.1ms')
        h.setIP(intf=f'h{i+1}-eth0', ip=f"10.0.0.{i+2}/24")
        threading.Thread(target=iperf_client, args=(h, server_ip, server_port)).start()

    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    main()
