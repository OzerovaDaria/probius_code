#!/bin/bash

# update repositories
sudo apt-get update

# install iperf
sudo apt-get install -y iperf3

# install a TCP service (web) and TCP ping
sudo apt-get install -y apache2 tcptraceroute bc
