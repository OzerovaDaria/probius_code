#!/bin/bash

sudo ovs-ofctl del-flows ovsbr0

sudo ovs-ofctl add-flow ovsbr0 in_port=1,actions=output:2,output:$1
sudo ovs-ofctl add-flow ovsbr0 in_port=2,actions=output:1,output:$1
