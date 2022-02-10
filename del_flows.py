#!/usr/bin/python3

import os
import psutil 

os.system("sudo ovs-ofctl del-flows vmbr0")
os.system("sudo ovs-ofctl add-flow vmbr0 action=normal")

