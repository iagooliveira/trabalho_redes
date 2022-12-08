#!/usr/bin/env python3

from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSController
from mininet.node import CPULimitedHost, Host, Node
from mininet.node import OVSKernelSwitch, UserSwitch
from mininet.node import IVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink, Intf
from subprocess import call

def myNetwork():

    net = Mininet( topo=None,
                   build=False,
                   ipBase='10.100.0.0/8')

    info( '*** Adding controller\n' )
    info( '*** Add switches\n')
    s1 = net.addSwitch('s1', cls=OVSKernelSwitch)
    s2 = net.addSwitch('s2', cls=OVSKernelSwitch)
    s3 = net.addSwitch('s3', cls=OVSKernelSwitch)
    s4 = net.addSwitch('s4', cls=OVSKernelSwitch)
    s5 = net.addSwitch('s5', cls=OVSKernelSwitch)
    s6 = net.addSwitch('s6', cls=OVSKernelSwitch)

    info( '*** Add hosts\n')
    h1 = net.addHost('h1', cls=Host, ip='10.0.0.1', defaultRoute=None, mac="00:00:00:00:00:01")
    h2 = net.addHost('h2', cls=Host, ip='10.0.0.2', defaultRoute=None, mac="00:00:00:00:00:02")
    h3 = net.addHost('h3', cls=Host, ip='10.0.0.3', defaultRoute=None, mac="00:00:00:00:00:03")
    h4 = net.addHost('h4', cls=Host, ip='10.0.0.4', defaultRoute=None, mac="00:00:00:00:00:04")
    h5 = net.addHost('h5', cls=Host, ip='10.0.0.5', defaultRoute=None, mac="00:00:00:00:00:05")
    h6 = net.addHost('h6', cls=Host, ip='10.0.0.6', defaultRoute=None, mac="00:00:00:00:00:06")
    h7 = net.addHost('h7', cls=Host, ip='10.0.0.7', defaultRoute=None, mac="00:00:00:00:00:07")
    h8 = net.addHost('h8', cls=Host, ip='10.0.0.8', defaultRoute=None, mac="00:00:00:00:00:08")
    h9 = net.addHost('h9', cls=Host, ip='10.0.0.9', defaultRoute=None, mac="00:00:00:00:00:09")

    info( '*** Add links\n')
    net.addLink(h1, s1)
    net.addLink(h2, s2)
    net.addLink(h3, s2)
    net.addLink(h4, s2)
    net.addLink(h5, s5)
    net.addLink(h6, s5)
    net.addLink(h7, s5)
    net.addLink(h8, s6)
    net.addLink(h9, s6)
    net.addLink(s2, s1)
    net.addLink(s1, s3)
    net.addLink(s3, s4)
    net.addLink(s5, s4)
    net.addLink(s6, s5)

    info( '*** Starting network\n')
    net.build()
    info( '*** Starting controllers\n')
    for controller in net.controllers:
        controller.start()

    info( '*** Starting switches\n')
    net.get('s1').start([])
    net.get('s2').start([])
    net.get('s3').start([])
    net.get('s4').start([])
    net.get('s5').start([])
    net.get('s6').start([])

    info( '*** Post configure switches and hosts\n')

    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    myNetwork()

