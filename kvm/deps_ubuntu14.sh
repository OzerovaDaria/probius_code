#!/bin/bash

# update repo
sudo apt-get update

# development tools
sudo apt-get install -y build-essential

# psutil
sudo apt-get install -y python-dev python-pip python-psutil

# trace-cmd
sudo apt-get install -y trace-cmd

# sqlite3
sudo apt-get install -y sqlite3 python-sqlite

# numpy, scipy, matplotlib, pandas, statsmodels
sudo apt-get install -y python-numpy python-scipy python-matplotlib python-pandas

# cloc
sudo apt-get install -y cloc

# graph-tool
sudo add-apt-repository -y ppa:ubuntu-toolchain-r/test
sudo apt-get update
sudo apt-key adv --keyserver pgp.skewed.de --recv-key 612DEFB798507F25
echo "deb http://downloads.skewed.de/apt/trusty trusty universe" | sudo tee -a /etc/apt/sources.list
echo "deb-src http://downloads.skewed.de/apt/trusty trusty universe" | sudo tee -a /etc/apt/sources.list
sudo apt-get update
sudo apt-get install -y python-graph-tool
