from mininet.net import Mininet
from mininet.topo import Topo
from mininet.node import OVSKernelSwitch    
from mininet.cli import CLI
from mininet.node import Host
from mininet.log import setLogLevel, info
from mininet.link import TCLink

class ManyHostsTopology(Topo):
    def build(self):
        switch = self.addSwitch('s1', cls=OVSKernelSwitch, failMode='standalone')
        
        for i in range(1, 65):
            host = self.addHost(f'h{i}', cls=Host, defaultRoute=None)
            self.addLink(host, switch, cls=TCLink, bw=1000, delay='0.1ms', loss=0.1)

def main():
    topo = ManyHostsTopology()
    net = Mininet(topo=topo, autoSetMacs=True, build=False, ipBase="10.0.0.0/24")

    net.start()

    # 호스트 IP 설정
    for i in range(1, 65):
        host = net.getNodeByName(f'h{i}')
        host.setIP(intf=f'h{i}-eth0', ip=f"10.0.0.{i}/24")

    net.pingAll()
    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    main()
