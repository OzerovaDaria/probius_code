#!/bin/bash

# install KVM
sudo apt-get install -y qemu-kvm libvirt-bin ubuntu-vm-builder bridge-utils uuid \
                        linux-tools-common linux-tools-`uname -r` linux-tools-virtual \
                        virt-manager

# install Open vSwitch
sudo apt-get install -y openvswitch-switch
