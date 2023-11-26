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


class ManyTCPConnectionTopology(Topo):
    def build(self):
        server = self.addHost('server', cls=Host, defaultRoute=None)
        switch = self.addSwitch('s1', cls=OVSKernelSwitch, failMode='standalone')

        self.addLink(server, switch, cls=TCLink, bw=10000000, delay='0.1ms', loss=0.01)


    

def main():
    topo = ManyTCPConnectionTopology()
    net = Mininet(topo=topo, autoSetMacs=True, build=False, ipBase="10.0.0.0/24")

    net.start()

    server = net.getNodeByName('server')
    server_port = 12000
    server_ip = "10.0.0.1"
    server.setIP(intf="server-eth0", ip="10.0.0.1/24")
    #server.cmd(f'python3 server_tcp.py {server_ip} {server_port} &')

    #time.sleep(3)

    clients = []
    threads = []
    for i in range(64):
        h = net.addHost(f'h{i+1}', cls=Host, defaultRoute=None)
        link = net.addLink(h, net.get('s1'), cls=TCLink, bw=1000000, delay='0.1ms', loss=0.01)
        h.setIP(intf=f'h{i+1}-eth0', ip=f"10.0.0.{i+2}/24")
        clients.append(h)    

   



    net.pingAll()

    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    main()
