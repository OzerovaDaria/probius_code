# General libraries
import os
import time
import psutil
#import libvirt
import threading
import subprocess
from xml.dom import minidom
from xml.etree import ElementTree
from datetime import datetime

# Probius libraries
import util
import vnf_mgmt
import database
import json
import kvm

guest_vnf_info = {}
host_vnf_info = {}
host_ext_info = {}
host_info = {}
host_nic = {}

proxmoxx = kvm.KVM()
proxmoxx.connect("172.30.12.2", "w4")


def get_info_of_VNF(resp1):
    #state, maxmem, mem, num_cpus, cpu_time = dom.info()
    num_cpus = resp1["cpus"]
    mem = resp1["ballooninfo"]["total_mem"]
    mem /= 1024. # KB -> MB
    #cpu_time /= 1000000000. # ns -> sec

    return num_cpus, mem


def get_cpu_stats_of_VNF(dom):
    stats = {}
    '''
    cpu_stats = dom.getCPUStats(True)

    cpu_time = cpu_stats[0]["cpu_time"] / 1000000000. # ns -> sec
    system_time = cpu_stats[0]["system_time"] / 1000000000. # ns -> sec
    user_time = cpu_stats[0]["user_time"] / 1000000000. # ns -> sec

    vcpu_stats = dom.getCPUStats(False)
    vcpu_time = 0.0
    for cpu in vcpu_stats:
        vcpu_time += cpu['vcpu_time']
    vcpu_time /= 1000000000. # ns -> sec
    '''
    stats["cpu_time"] = 0 #cpu_time
    stats["vcpu_time"] = 0 #vcpu_time
    stats["user_time"] = 0 #user_time
    stats["system_time"] = 0 #system_time

    return stats

def get_mem_stats_of_VNF(resp1):
    #stats = dom.memoryStats()
    stats = {}
    stats["actual"] = resp1["ballooninfo"]["actual"]
    stats["swap_in"] = resp1["ballooninfo"]["mem_swapped_in"]
    stats["actual"] /= 1024. # KB -> MB
    stats["swap_in"] /= 1024. # KB -> MB
    stats["rss"] = 0. # KB -> MB

    return stats

def get_disk_stats_of_VNF(resp1):
    stats = {}
    stats["read_count"] = resp1["blockstat"]["scsi0"]["rd_operations"] * 1.0
    stats["read_bytes"] = resp1["blockstat"]["scsi0"]["rd_bytes"] * 1.0
    stats["write_count"] = resp1["blockstat"]["scsi0"]["wr_operations"] * 1.0
    stats["write_bytes"] = resp1["blockstat"]["scsi0"]["wr_bytes"] * 1.0

    stats["error"] = (resp1["blockstat"]["scsi0"]["failed_wr_operations"] + resp1["blockstat"]["scsi0"]["failed_rd_operations"]) * 1.0
    
    return stats

def get_net_stats_of_VNF(dom):
    stats = {}
    '''
    tree = ElementTree.fromstring(dom.XMLDesc())
    ifaces = tree.findall('devices/interface/target')
    for dev in ifaces:
        iface = dev.get('dev')

        intf = str(iface)
    '''
    intf = "ens18"
    stats[intf] = {}

    #istats = dom.interfaceStats(iface)

    stats[intf]["packets_recv"] = resp1["statistics"]["rx-packets"] * 1.0
    stats[intf]["bytes_recv"] = resp1["statistics"]["rx-bytes"] * 1.0
    stats[intf]["packets_sent"] = resp1["statistics"]["tx-packets"] * 1.0
    stats[intf]["bytes_sent"] = resp1["statistics"]["tx-bytes"] * 1.0

    return stats

# libvirt
def monitor_VNF(config, vnf):
    vnf_stats = {}
    vmid = config[vnf]["vmid"]
    resp1 = proxmoxx.proxmox().nodes('w4').qemu(vmid).status.current.get()
    #print("maxmem", resp1["maxmem"])
    b = json.dumps(resp1, indent=2)
    #print(b)
    print("STATUS = ", resp1["status"])
    print("MEM = ", resp1["mem"])
    print("CPUS = ", resp1["cpus"])
    print("ACTUAL MEM = ", resp1["ballooninfo"]["actual"])
    print("MEM SWAP_IN = ", resp1["ballooninfo"]["mem_swapped_in"])
    print("DISC_READ_COUNT = ", resp1["blockstat"]["scsi0"]["rd_operations"])
    print("DISC_WRITE_COUNT = ", resp1["blockstat"]["scsi0"]["wr_operations"])
    print("DISC_READ_BYTES = ", resp1["blockstat"]["scsi0"]["rd_bytes"])
    print("DISC_WRITE_BYTES = ", resp1["blockstat"]["scsi0"]["wr_bytes"])
    print("$$$$$$$$$$$$$$$$$$$$$$$$$$")
    '''    
    conn = libvirt.open("qemu:///system")
    if conn == None:
        print ("Error: failed to connect QEMU")
    else:
        dom = conn.lookupByName(vnf)
    '''
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print (str(vnf) + " monitors start: " + str(timestamp))

    num_cpus, mem = get_info_of_VNF(resp1)
    print("num_cpus, mem = ", num_cpus, mem)
    print()
    vnf_stats["cpu_num"] = str(num_cpus)

    first = False
        
    if guest_vnf_info[vnf]["time"] == 0.0:
        first = True

    tm = time.time()
    
    cpu_stats = get_cpu_stats_of_VNF(resp1)

    if first == False:
        vnf_stats["cpu_time"] = str((cpu_stats["cpu_time"] - guest_vnf_info[vnf]["cpu_time"]) \
                                     / (tm - guest_vnf_info[vnf]["time"]))
        vnf_stats["vcpu_time"] = str((cpu_stats["vcpu_time"] - guest_vnf_info[vnf]["vcpu_time"]) \
                                     / (tm - guest_vnf_info[vnf]["time"]))
        vnf_stats["user_time"] = str((cpu_stats["user_time"] - guest_vnf_info[vnf]["user_time"]) \
                                     / (tm - guest_vnf_info[vnf]["time"]))
        vnf_stats["system_time"] = str((cpu_stats["system_time"] - guest_vnf_info[vnf]["system_time"]) \
                                     / (tm - guest_vnf_info[vnf]["time"]))

    guest_vnf_info[vnf]["cpu_time"] = cpu_stats["cpu_time"]
    guest_vnf_info[vnf]["vcpu_time"] = cpu_stats["vcpu_time"]
    guest_vnf_info[vnf]["user_time"] = cpu_stats["user_time"]
    guest_vnf_info[vnf]["system_time"] = cpu_stats["system_time"]
    
    mem_stats = get_mem_stats_of_VNF(resp1)

    vnf_stats["total_mem"] = str(mem)
    vnf_stats["rss_mem"] = 0 #str(mem_stats["rss"])

    disk_stats = get_disk_stats_of_VNF(resp1)
    print("disk_stats[read_count] = ", disk_stats["read_count"])
    
    if first == False:
        vnf_stats["read_count"] = str((disk_stats["read_count"] - guest_vnf_info[vnf]["read_count"]) \
                                       / (tm - guest_vnf_info[vnf]["time"]))
        vnf_stats["read_bytes"] = str((disk_stats["read_bytes"] - guest_vnf_info[vnf]["read_bytes"]) \
                                       / (tm - guest_vnf_info[vnf]["time"]))
        vnf_stats["write_count"] = str((disk_stats["write_count"] - guest_vnf_info[vnf]["write_count"]) \
                                       / (tm - guest_vnf_info[vnf]["time"]))
        vnf_stats["write_bytes"] = str((disk_stats["write_bytes"] - guest_vnf_info[vnf]["write_bytes"]) \
                                       / (tm - guest_vnf_info[vnf]["time"]))

    guest_vnf_info[vnf]["read_count"] = disk_stats["read_count"]
    guest_vnf_info[vnf]["read_bytes"] = disk_stats["read_bytes"]
    guest_vnf_info[vnf]["write_count"] = disk_stats["write_count"]
    guest_vnf_info[vnf]["write_bytes"] = disk_stats["write_bytes"]
    
    net_stats = get_net_stats_of_VNF(resp1)

    for intf in net_stats:
        if intf == "ens18" #config[vnf]["inbound"]: #?????????????????
            if first == False:
                vnf_stats["packets_recv"] = str((net_stats[intf]["packets_recv"] - guest_vnf_info[vnf]["packets_recv"]) \
                                                 / (tm - guest_vnf_info[vnf]["time"]))
                vnf_stats["bytes_recv"] = str((net_stats[intf]["bytes_recv"] - guest_vnf_info[vnf]["bytes_recv"]) \
                                                 / (tm - guest_vnf_info[vnf]["time"]))

            guest_vnf_info[vnf]["packets_recv"] = net_stats[intf]["packets_recv"]
            guest_vnf_info[vnf]["bytes_recv"] = net_stats[intf]["bytes_recv"]

            if first == False:
                if config[vnf]["outbound"] == "":
                    vnf_stats["packets_sent"] = str((net_stats[intf]["packets_sent"] - guest_vnf_info[vnf]["packets_sent"]) \
                                                     / (tm - guest_vnf_info[vnf]["time"]))
                    vnf_stats["bytes_sent"] = str((net_stats[intf]["bytes_sent"] - guest_vnf_info[vnf]["bytes_sent"]) \
                                                     / (tm - guest_vnf_info[vnf]["time"]))

            if config[vnf]["outbound"] == "": #?????????????????????
                guest_vnf_info[vnf]["packets_sent"] = net_stats[intf]["packets_sent"]
                guest_vnf_info[vnf]["bytes_sent"] = net_stats[intf]["bytes_sent"]
        elif intf == config[vnf]["outbound"]:
            if first == False:
                vnf_stats["packets_sent"] = str((net_stats[intf]["packets_sent"] - guest_vnf_info[vnf]["packets_sent"]) \
                                                 / (tm - guest_vnf_info[vnf]["time"]))
                vnf_stats["bytes_sent"] = str((net_stats[intf]["bytes_sent"] - guest_vnf_info[vnf]["bytes_sent"]) \
                                                 / (tm - guest_vnf_info[vnf]["time"]))

            guest_vnf_info[vnf]["packets_sent"] = net_stats[intf]["packets_sent"]
            guest_vnf_info[vnf]["bytes_sent"] = net_stats[intf]["bytes_sent"]

    #conn.close()

    if first == False:
        database.guest_vnf_info(vnf, timestamp, vnf_stats)

    guest_vnf_info[vnf]["time"] = tm
    
    return

# inserted
def monitor_host_VNF(config, vnf):
    vnf_stats = {}

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    #print "host-side " + vnf + " monitor starts: " + str(timestamp)

    vnf_stats["pid"] = str(config[vnf]["pid"])

    p = psutil.Process(config[vnf]["pid"])

    # cpu_num
    vnf_stats["cpu_num"] = str(len(p.cpu_affinity()))

    # cpu_affinity
    affinity = p.cpu_affinity()

    vnf_stats["cpu_affinity"] = ""
    for index in range(len(affinity)):
        if vnf_stats["cpu_affinity"] == "":
            vnf_stats["cpu_affinity"] = str(affinity[index])
        else:
            vnf_stats["cpu_affinity"] = vnf_stats["cpu_affinity"] + "," + str(affinity[index])

    # cpu_percent
    vnf_stats["cpu_percent"] = str(p.cpu_percent(interval=0.5))

    first = False
    if host_vnf_info[vnf]["time"] == 0.0:
        first = True

    tm = time.time()

    # user_time, system_time
    cpu_times = p.cpu_times()
    user_time = cpu_times[0]
    system_time = cpu_times[1]
    
    if first == False:
        vnf_stats["user_time"] = str((user_time - host_vnf_info[vnf]["user_time"]) / (tm - host_vnf_info[vnf]["time"]))
        vnf_stats["system_time"] = str((system_time - host_vnf_info[vnf]["system_time"]) / (tm - host_vnf_info[vnf]["time"]))

    host_vnf_info[vnf]["user_time"] = user_time
    host_vnf_info[vnf]["system_time"] = system_time

    # mem_percent
    vnf_stats["mem_percent"] = str(p.memory_percent())

    # total_mem, rss_mem
    mi = p.memory_info()
    print(mi)
    rss = mi[0]
    vms = mi[1]

    vnf_stats["total_mem"] = str(int(config[vnf]["mem"]) * 1.0)
    vnf_stats["rss_mem"]  = str(rss / (1024. * 1024.))

    # io counter
    if os.getuid() == 0:
        io_counters =  p.io_counters()

        read_count = io_counters[0]
        read_bytes = io_counters[1]
        write_count = io_counters[2]
        write_bytes = io_counters[3]

        if first == False:
            vnf_stats["read_count"] = str((read_count * 1.0 - host_vnf_info[vnf]["read_count"]) / (tm - host_vnf_info[vnf]["time"]))
            vnf_stats["read_bytes"] = str((read_bytes * 1.0 - host_vnf_info[vnf]["read_bytes"]) / (tm - host_vnf_info[vnf]["time"]))
            vnf_stats["write_count"] = str((write_count * 1.0 - host_vnf_info[vnf]["write_count"]) / (tm - host_vnf_info[vnf]["time"]))
            vnf_stats["write_bytes"] = str((write_bytes * 1.0 - host_vnf_info[vnf]["write_bytes"]) / (tm - host_vnf_info[vnf]["time"]))

        host_vnf_info[vnf]["read_count"] = read_count * 1.0
        host_vnf_info[vnf]["read_bytes"] = read_bytes * 1.0
        host_vnf_info[vnf]["write_count"] = write_count * 1.0
        host_vnf_info[vnf]["write_bytes"] = write_bytes * 1.0
    else:
        vnf_stats["read_count"] = "0.0"
        vnf_stats["read_bytes"] = "0.0"
        vnf_stats["write_count"] = "0.0"
        vnf_stats["write_bytes"] = "0.0"

    # num_threads
    vnf_stats["num_threads"] = str(p.num_threads() * 1.0)

    # context switches
    ctx_sw = p.num_ctx_switches()
    vol_ctx = ctx_sw[0]
    invol_ctx = ctx_sw[1]

    if first == False:
        vnf_stats["vol_ctx"] = str((vol_ctx * 1.0 - host_vnf_info[vnf]["vol_ctx"]) / (tm - host_vnf_info[vnf]["time"]))
        vnf_stats["invol_ctx"] = str((invol_ctx * 1.0 - host_vnf_info[vnf]["invol_ctx"]) / (tm - host_vnf_info[vnf]["time"]))

    host_vnf_info[vnf]["vol_ctx"] = vol_ctx * 1.0
    host_vnf_info[vnf]["invol_ctx"] = invol_ctx * 1.0

    # insert vnf_info
    if first == False:
        database.host_VNF_info(vnf, timestamp, vnf_stats)

    host_vnf_info[vnf]["time"] = tm
    print("vnf_stats", vnf_stats)

    print("host_vnf_info", host_vnf_info)

    return

# inserted
def monitor_host_extra(config, extra):
    ext_stats = {}

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    #print "host-side " + extra["name"] + "(" + str(extra["pid"]) + ") monitor starts: " + str(timestamp)

    ext_stats["name"] = extra["name"]

    pid = extra["pid"]
    ext_stats["pid"] = extra["pid"]

    p = psutil.Process(pid)

    # cpu_num
    ext_stats["cpu_num"] = str(len(p.cpu_affinity()))

    # cpu_affinity
    affinity = p.cpu_affinity()

    ext_stats["cpu_affinity"] = ""
    for index in range(len(affinity)):
        if ext_stats["cpu_affinity"] == "":
            ext_stats["cpu_affinity"] = str(affinity[index])
        else:
            ext_stats["cpu_affinity"] = ext_stats["cpu_affinity"] + "," + str(affinity[index])

    # cpu_percent
    ext_stats["cpu_percent"] = str(p.cpu_percent(interval=0.5))

    first = False
    if host_ext_info[pid]["time"] == 0.0:
        first = True

    tm = time.time()

    # user_time, system_time
    cpu_times = p.cpu_times()
    user_time = cpu_times[0]
    system_time = cpu_times[1]

    if first == False:
        ext_stats["user_time"] = str((user_time - host_ext_info[pid]["user_time"]) / (tm - host_ext_info[pid]["time"]))
        ext_stats["system_time"] = str((system_time - host_ext_info[pid]["system_time"]) / (tm - host_ext_info[pid]["time"]))

    host_ext_info[pid]["user_time"] = user_time
    host_ext_info[pid]["system_time"] = system_time

    # mem_percent
    ext_stats["mem_percent"] = str(p.memory_percent())

    # io counter
    if os.getuid() == 0:
        io_counters = p.io_counters()
        read_count = io_counters[0]
        read_bytes = io_counters[1]
        write_count = io_counters[2]
        write_bytes = io_counters[3]

        if first == False:
            ext_stats["read_count"] = str((read_count * 1.0 - host_ext_info[pid]["read_count"]) / (tm - host_ext_info[pid]["time"]))
            ext_stats["read_bytes"] = str((read_bytes * 1.0 - host_ext_info[pid]["read_bytes"]) / (tm - host_ext_info[pid]["time"]))
            ext_stats["write_count"] = str((write_count * 1.0 - host_ext_info[pid]["write_count"]) / (tm - host_ext_info[pid]["time"]))
            ext_stats["write_bytes"] = str((write_bytes * 1.0 - host_ext_info[pid]["write_bytes"]) / (tm - host_ext_info[pid]["time"]))
    
        host_ext_info[pid]["read_count"] = read_count * 1.0
        host_ext_info[pid]["read_bytes"] = read_bytes * 1.0
        host_ext_info[pid]["write_count"] = write_count * 1.0
        host_ext_info[pid]["write_bytes"] = write_bytes * 1.0
    else:
        ext_stats["read_count"] = "0.0"
        ext_stats["read_bytes"] = "0.0"
        ext_stats["write_count"] = "0.0"
        ext_stats["write_bytes"] = "0.0"

    # num_threads
    ext_stats["num_threads"] = str(p.num_threads() * 1.0)

    # context switches
    ctx_switches = p.num_ctx_switches()
    vol_ctx = ctx_switches[0]
    invol_ctx = ctx_switches[1]

    if first == False:
        ext_stats["vol_ctx"] = str((vol_ctx * 1.0 - host_ext_info[pid]["vol_ctx"]) / (tm - host_ext_info[pid]["time"]))
        ext_stats["invol_ctx"] = str((invol_ctx * 1.0 - host_ext_info[pid]["invol_ctx"]) / (tm - host_ext_info[pid]["time"]))

    host_ext_info[pid]["vol_ctx"] = vol_ctx * 1.0
    host_ext_info[pid]["invol_ctx"] = invol_ctx * 1.0

    # insert ext_info
    if first == False:
        database.host_ext_info(timestamp, ext_stats)

    host_ext_info[pid]["time"] = tm

    print("ext_stats", ext_stats)
    print("host_ext_info", host_ext_info)
    return

# inserted
# psutil
def monitor_host(profile):
    host_stats = {}

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print ("host monitor starts: " + str(timestamp))

    first = False
    if host_info["time"] == 0.0:
        first = True

    # cpu_percent
    host_stats["cpu_percent"] = psutil.cpu_percent(interval=0.5)

    tm = time.time()

    # cpu_times
    cpu_times = psutil.cpu_times()
    user = cpu_times[0] 
    nice = cpu_times[1] 
    system = cpu_times[2] 
    idle = cpu_times[3] 
    iowait = cpu_times[4] 
    irq = cpu_times[5] 
    softirq = cpu_times[6] 
    steal = cpu_times[7] 
    guest = cpu_times[8] 
    guest_nice = cpu_times[9] 

    if first == False:
        host_stats["user_time"] = str((user - host_info["user_time"]) / (tm - host_info["time"]))
        host_stats["nice_time"] = str((nice - host_info["nice_time"]) / (tm - host_info["time"]))
        host_stats["system_time"] = str((system - host_info["system_time"]) / (tm - host_info["time"]))
        host_stats["idle_time"] = str((idle - host_info["idle_time"]) / (tm - host_info["time"]))
        host_stats["iowait_time"] = str((iowait - host_info["iowait_time"]) / (tm - host_info["time"]))
        host_stats["irq_time"] = str((irq - host_info["irq_time"]) / (tm - host_info["time"]))
        host_stats["softirq_time"] = str((softirq - host_info["softirq_time"]) / (tm - host_info["time"]))
        host_stats["steal_time"] = str((steal - host_info["steal_time"]) / (tm - host_info["time"]))
        host_stats["guest_time"] = str((guest - host_info["guest_time"]) / (tm - host_info["time"]))
        host_stats["guest_nice_time"] = str((guest_nice - host_info["guest_nice_time"]) / (tm - host_info["time"]))

    host_info["user_time"] = user
    host_info["nice_time"] = nice
    host_info["system_time"] = system
    host_info["idle_time"] = idle
    host_info["iowait_time"] = iowait
    host_info["irq_time"] = irq
    host_info["softirq_time"] = softirq
    host_info["steal_time"] = steal
    host_info["guest_time"] = guest
    host_info["guest_nice_time"] = guest_nice

    # mem_percent, total_mem, used_mem, available_mem
    virt_mem = psutil.virtual_memory()
    total_mem = virt_mem[0]
    available_mem = virt_mem[1]
    mem_percent = virt_mem[2]
    used_mem = virt_mem[3]
    free_mem = virt_mem[4]
    active_mem = virt_mem[5]
    inactive_mem = virt_mem[6]
    buffers_mem = virt_mem[7]
    cached_mem = virt_mem[8]
    
    host_stats["mem_percent"] = str(mem_percent)

    host_stats["total_mem"] = str(total_mem / (1024. * 1024.))
    host_stats["available_mem"] = str(available_mem / (1024. * 1024.))
    host_stats["used_mem"] = str(used_mem / (1024. * 1024.))
    host_stats["free_mem"] = str(free_mem / (1024. * 1024.))
    host_stats["active_mem"] = str(active_mem / (1024. * 1024.))
    host_stats["inactive_mem"] = str(inactive_mem / (1024. * 1024.))
    host_stats["buffers_mem"] = str(buffers_mem / (1024. * 1024.))
    host_stats["cached_mem"] = str(cached_mem / (1024. * 1024.))

    read_count, write_count, read_bytes, write_bytes, read_time, write_time, rmc, wmc, hzc = psutil.disk_io_counters()

    if first == False:
        host_stats["read_count"] = str((read_count * 1.0 - host_info["read_count"]) / (tm - host_info["time"]))
        host_stats["read_bytes"] = str((read_bytes * 1.0 - host_info["read_bytes"]) / (tm - host_info["time"]))
        host_stats["write_count"] = str((write_count * 1.0 - host_info["write_count"]) / (tm - host_info["time"]))
        host_stats["write_bytes"] = str((write_bytes * 1.0 - host_info["write_bytes"]) / (tm - host_info["time"]))

    host_info["read_count"] = read_count * 1.0
    host_info["read_bytes"] = read_bytes * 1.0
    host_info["write_count"] = write_count * 1.0
    host_info["write_bytes"] = write_bytes * 1.0

    if first == False:
        database.host_info(timestamp, host_stats)

    interfaces = psutil.net_io_counters(pernic=True)
    for interface in interfaces:
        host_nets = {}
        '''
        if interface == profile["inbound"] or interface == profile["outbound"]:
            bytes_sent, bytes_recv, packets_sent, packets_recv, \
                errin, errout, dropin, dropout = interfaces[interface]

            if interface in host_nic:
                host_nets["interface"] = interface
                host_nets["packets_recv"] = str(((packets_recv - host_nic[interface]["packets_recv"]) * 1.0) \
                                                  / (tm - host_info["time"]))
                host_nets["bytes_recv"] = str(((bytes_recv - host_nic[interface]["bytes_recv"]) * 1.0) \
                                                  / (tm - host_info["time"]))
                host_nets["packets_sent"] = str(((packets_sent - host_nic[interface]["packets_sent"]) * 1.0) \
                                                  / (tm - host_info["time"]))
                host_nets["bytes_sent"] = str(((bytes_sent - host_nic[interface]["bytes_sent"]) * 1.0) \
                                                  / (tm - host_info["time"]))
            else:
                host_nic[interface] = {}

            host_nic[interface]["packets_recv"] = packets_recv
            host_nic[interface]["bytes_recv"] = bytes_recv
            host_nic[interface]["packets_sent"] = packets_sent
            host_nic[interface]["bytes_sent"] = bytes_sent

            if "interface" in host_nets:
                database.host_net(timestamp, host_nets)

        elif "vnet" in interface:
            bytes_sent, bytes_recv, packets_sent, packets_recv, \
                errin, errout, dropin, dropout = interfaces[interface]

            if interface in host_nic:
                host_nets["interface"] = interface
                host_nets["packets_recv"] = str(((packets_recv - host_nic[interface]["packets_recv"]) * 1.0) \
                                                  / (tm - host_info["time"]))
                host_nets["bytes_recv"] = str(((bytes_recv - host_nic[interface]["bytes_recv"]) * 1.0) \
                                                  / (tm - host_info["time"]))
                host_nets["packets_sent"] = str(((packets_sent - host_nic[interface]["packets_sent"]) * 1.0) \
                                                  / (tm - host_info["time"]))
                host_nets["bytes_sent"] = str(((bytes_sent - host_nic[interface]["bytes_sent"]) * 1.0) \
                                                  / (tm - host_info["time"]))
            else:
                host_nic[interface] = {}

            host_nic[interface]["packets_recv"] = packets_recv
            host_nic[interface]["bytes_recv"] = bytes_recv
            host_nic[interface]["packets_sent"] = packets_sent
            host_nic[interface]["bytes_sent"] = bytes_sent

            if "interface" in host_nets:
                database.host_net(timestamp, host_nets)

        elif "tap" in interface:
            bytes_sent, bytes_recv, packets_sent, packets_recv, \
                errin, errout, dropin, dropout = interfaces[interface]

            if interface in host_nic:
                host_nets["interface"] = interface
                host_nets["packets_recv"] = str(((packets_recv - host_nic[interface]["packets_recv"]) * 1.0) \
                                                  / (tm - host_info["time"]))
                host_nets["bytes_recv"] = str(((bytes_recv - host_nic[interface]["bytes_recv"]) * 1.0) \
                                                  / (tm - host_info["time"]))
                host_nets["packets_sent"] = str(((packets_sent - host_nic[interface]["packets_sent"]) * 1.0) \
                                                  / (tm - host_info["time"]))
                host_nets["bytes_sent"] = str(((bytes_sent - host_nic[interface]["bytes_sent"]) * 1.0) \
                                                  / (tm - host_info["time"]))
            else:
                host_nic[interface] = {}

            host_nic[interface]["packets_recv"] = packets_recv
            host_nic[interface]["bytes_recv"] = bytes_recv
            host_nic[interface]["packets_sent"] = packets_sent
            host_nic[interface]["bytes_sent"] = bytes_sent

            if "interface" in host_nets:
                database.host_net(timestamp, host_nets)
        '''
    host_info["time"] = tm
    print("host_stats: ",host_stats)

    print("host_info: ",host_info)
    return
			
		

def create_monitor_threads_per_VNF(profile, config, VNFs, extras):
    threads = []

    # host monitor
    t = threading.Thread(target=monitor_host, args=(profile,))
    threads.append(t)

    # host-side VNF monitor
    for vnf in VNFs:
        t = threading.Thread(target=monitor_host_VNF, args=(config, vnf,))
        threads.append(t)

    # host-side extra monitor
    for extra in extras:
        t = threading.Thread(target=monitor_host_extra, args=(config, extra,))
        threads.append(t)
    '''
    # guest-side VNF monitor
    for vnf in VNFs:
        t = threading.Thread(target=monitor_VNF, args=(config, vnf,))
        threads.append(t)
    '''
    # start threads
    for thread in threads:
        thread.start()

    return

def initialize_VNF_statistics(VNFs, extras):
    guest_vnf_info.clear()
    host_vnf_info.clear()
    host_ext_info.clear()

    host_info.clear()
    host_nic.clear()

    for vnf in VNFs:
        guest_vnf_info[vnf] = {}
        guest_vnf_info[vnf]["time"] = 0.0

        host_vnf_info[vnf] = {}
        host_vnf_info[vnf]["time"] = 0.0

        host_info["time"] = 0.0

    for extra in extras:
        host_ext_info[extra["pid"]] = {}
        host_ext_info[extra["pid"]]["time"] = 0.0

    print("GUEST_VNF_INFO")
    print(guest_vnf_info)
    print("HOST_VNF_INFO")
    print(host_vnf_info)
    return


def monitor_VNFs(profile, config, VNFs, extras, monitor_time, monitored=0):
    monitored += 1

    create_monitor_threads_per_VNF(profile, config, VNFs, extras)

    if monitored < monitor_time:
        threading.Timer(1, monitor_VNFs, args=(profile, config, VNFs, extras, monitor_time, monitored)).start()

    time.sleep((monitor_time - monitored) * 1.0)

    return
