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

        self.addLink(server, switch, cls=TCLink, bw=1000, delay='0.1ms', loss=0.01)

        for i in range(1, 65):
            host = self.addHost(f'h{i}', cls=Host, defaultRoute=None)
            self.addLink(host, switch, cls=TCLink, bw=1000, delay='0.1ms', loss=0.01)




def ping_to_server(net, client, server):
    print(f"{client.IP()} -> s{server.IP()}")
    result = client.cmd(f"ping -c1 {server.IP()}")
    print(result)
    all_output = net._parsePingFull( result )
    print(all_output)


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
    for i in range(1, 65):
        h = net.getNodeByName(f'h{i}')
        h.setIP(intf=f'h{i+1}-eth0', ip=f"10.0.0.{i+2}/24")
        clients.append(h)  


    for client in clients:
        t = threading.Thread(target=ping_to_server, args=(net, client, server))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()
    
    src, dst = net.hosts[0], net.hosts[1]
    s_bw, c_bw = net.iperf([src, dst], seconds=10)
    info(s_bw)

    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    main()
