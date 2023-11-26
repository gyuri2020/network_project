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

        self.addLink(server, switch, cls=TCLink, bw=10000000, delay='0.1ms', loss=0.01)

def iperf_client(host, server_ip, port, bandwidth):
    host.cmd(f"iperf -c {server_ip} -p {port} -t 10 &")

def measure_connection(net, client, server_ip):
    client_bw, _ = net.iperf([client, net.getNodeByName('server')], seconds=10)
    server_bw, _ = net.iperf([net.getNodeByName('server'), client], seconds=10)
    
    client_loss = client.cmd(f"ping -c 10 {server_ip} | grep packet | awk '{{print $6}}'")
    server_loss = net.getNodeByName('server').cmd(f"ping -c 10 {client.IP()} | grep packet | awk '{{print $6}}'")
    
    client_rtt = client.cmd(f"ping -c 10 {server_ip} | grep rtt | awk '{{print $4}}'")
    server_rtt = net.getNodeByName('server').cmd(f"ping -c 10 {client.IP()} | grep rtt | awk '{{print $4}}'")

    info(f"Client {client} to Server - Bandwidth: {client_bw}, Loss: {client_loss}, RTT: {client_rtt}")
    info(f"Server to Client {client} - Bandwidth: {server_bw}, Loss: {server_loss}, RTT: {server_rtt}")

def main():
    topo = ManyTCPConnectionTopology()
    net = Mininet(topo=topo, autoSetMacs=True, build=False, ipBase="10.0.0.0/24")

    net.start()

    server = net.getNodeByName('server')
    server.setIP(intf="server-eth0", ip="10.0.0.1/24")

    server_ip = "10.0.0.1"
    server_port = 5001

    clients = []
    for i in range(64):
        h = net.addHost(f'h{i+1}', cls=Host, defaultRoute=None)
        link = net.addLink(h, net.get('s1'), cls=TCLink, bw=int(f"{i}0000"), delay='0.1ms', loss=0.01)
        h.setIP(intf=f'h{i+1}-eth0', ip=f"10.0.0.{i+2}/24")
        clients.append(h)
        threading.Thread(target=iperf_client, args=(h, server_ip, server_port, f"{i}0000")).start()

        bw = link.intf1.params['bw']
        delay = link.intf1.params['delay']
        loss = link.intf1.params['loss']

        info(f"Link {i+1} - Bandwidth: {bw}, Delay: {delay}, Loss: {loss}\n")

    # 각 connection의 대역폭, 손실률, RTT 계산
    for client in clients:
        threading.Thread(target=measure_connection, args=(net, client, server_ip)).start()

    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    main()
