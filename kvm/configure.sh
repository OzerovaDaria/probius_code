#!/bin/bash

# stop the default network
virsh net-destroy default

# edit the default network
virsh net-edit default

# start the default network
virsh net-start default

# set the autostart flag of the default network
virsh net-autostart default

# remove and add ovsbr0
sudo ovs-vsctl del-br ovsbr0 2> /dev/null
sudo ovs-vsctl add-br ovsbr0

# configure ovsbr0
sudo ovs-vsctl set-controller ovsbr0 tcp:127.0.0.1:6633
sudo ovs-vsctl -- set bridge ovsbr0 protocols=OpenFlow10
sudo ovs-vsctl set-fail-mode ovsbr0 secure

# add interfaces to ovsbr0
sudo ovs-vsctl add-port ovsbr0 ens4f0 # inbound interface
sudo ovs-vsctl add-port ovsbr0 ens4f1 # outbound interface

# add ovsbr0 to KVM networks
virsh net-define ovsbr0.xml

# start ovsbr0 in KVM networks
virsh net-start ovsbr0

# set the autostart flag of ovsbr0 in KVM networks
virsh net-autostart ovsbr0
