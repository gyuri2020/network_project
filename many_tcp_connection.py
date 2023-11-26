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

        self.addLink(server, switch, cls=TCLink, bw=1000, delay='0.1ms', loss=0.01)

def iperf_client(host, server_ip, port):
    host.cmd(f"iperf -c {server_ip} -p {port} -t 10")

def measure_connection(net, client, server_ip):
    bw_result = net.iperf([client, net.getNodeByName('server')], seconds=10)
    info(f"{client} {bw_result}")

def main():
    topo = ManyTCPConnectionTopology()
    net = Mininet(topo=topo, autoSetMacs=True, build=False, ipBase="10.0.0.0/24")

    net.start()

    server = net.getNodeByName('server')
    server.setIP(intf="server-eth0", ip="10.0.0.1/24")

    server_ip = "10.0.0.1"
    server_port = 5001

    clients = []
    threads = []
    for i in range(64):
        h = net.addHost(f'h{i+1}', cls=Host, defaultRoute=None)
        link = net.addLink(h, net.get('s1'), cls=TCLink, bw=int(f"{i}0"), delay='0.1ms', loss=0.01)
        h.setIP(intf=f'h{i+1}-eth0', ip=f"10.0.0.{i+2}/24")
        clients.append(h)

        bw = link.intf1.params['bw']
        delay = link.intf1.params['delay']
        loss = link.intf1.params['loss']

        info(f"Link {i+1} - Bandwidth: {bw}, Delay: {delay}, Loss: {loss}\n")

    # 서버에서 iperf 유지
    server.cmd(f"iperf -s -p {server_port} &")

    # 각 connection의 대역폭, 손실률, RTT 계산
    for client in clients:
        thread = threading.Thread(target=iperf_client, args=(client, server_ip, server_port))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    # 클라이언트에서 10초 동안만 실행 후 종료
    for client in clients:
        measure_connection(net, client, server_ip)

    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    main()
