from mininet.net import Mininet
from mininet.topo import Topo
from mininet.node import OVSKernelSwitch
from mininet.cli import CLI
from mininet.node import Host
from mininet.log import setLogLevel, info
from mininet.link import TCLink
import threading
import time

class ManyTCPConnectionTopology(Topo):
    def build(self):
        server = self.addHost('server', cls=Host, defaultRoute=None)
        switch = self.addSwitch('s1', cls=OVSKernelSwitch, failMode='standalone')

        self.addLink(server, switch, cls=TCLink, bw=1000, delay='0.1ms', loss=0.01)

def iperf_client(net, host, server, port):
    print(f"Start")
    #result = host.cmd(f"iperf -c {server_ip} -p {port} -t 10")
    s_bw, c_bw = net.iperf([host, server], seconds=10, port=port)
    info(s_bw)
    print(f"End iperf")


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
    for i in range(1):
        h = net.addHost(f'h{i+1}', cls=Host, defaultRoute=None)
        port = server_port + i + 1  # 서로 다른 포트를 사용하도록 변경
        link = net.addLink(h, net.get('s1'), cls=TCLink, bw=int(f"{i+1}0"), delay='0.1ms', loss=0.01)
        h.setIP(intf=f'h{i+1}-eth0', ip=f"10.0.0.{i+2}/24")
        clients.append((h, port))

        bw = link.intf1.params['bw']
        delay = link.intf1.params['delay']
        loss = link.intf1.params['loss']

        info(f"Link {i+1} - Bandwidth: {bw}, Delay: {delay}, Loss: {loss}\n")



    time.sleep(5) 
    print("Start Client iperf")

    # 클라이언트들이 동시에 서버에 10초간 패킷을 전송
    for client, port in clients:
        print(f"Client {client.name} - Port: {port}")
        thread = threading.Thread(target=iperf_client, args=(client, server_ip, port))
        threads.append(thread)
        thread.start()
        

    for thread in threads:
        print("Join Thread")
        thread.join()

    print("End Client iperf3")
    # 서버에서 iperf3 종료
    server.cmd("killall iperf3")

    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    main()
