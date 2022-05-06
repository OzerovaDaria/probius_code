# General libraries
import os, time, json
import psutil 
#import libvirt
import subprocess
from datetime import datetime

# Probius libraries
import database
import kvm
proxmoxx = kvm.KVM()
proxmoxx.connect("172.30.12.2", "w4")
'''
vnf_dict = {}
vnf_dict["firewall"] = 200
vnf_dict["netsniff-ng"] = 201
vnf_dict["snort-ids"] = 202
vnf_dict["suricata-ids"] = 203
vnf_dict["suricata-ips"] = 204
vnf_dict["tcpdump"] = 205
vnf_dict["NAT"] = 206
'''
def load_VNF_configurations(conf_file):
    config = {}

    with open(conf_file) as data_file:
        data = json.load(data_file)

        for name in data:
            config[name] = {}

            config[name]["name"] = str(name) # VNF name in a configuration
            config[name]["type"] = str(data[name]["type"]) # passive or inline
            config[name]["vmid"] = data[name]["vmid"] # virtual machine ID
            config[name]["pid"] = "" # Process ID

            config[name]["net0"] = "" # mgmt virtual interface
            config[name]["net1"] = "" # inbound virtual interface
            config[name]["net2"] = "" # outbound virtual interface

            config[name]["inbound"] =  str(data[name]["inbound"]) # inbound physical interface
            config[name]["inbound_mac"] =  str(data[name]["inbound_mac"]) # inbound mac address
            config[name]["inbound_port"] = "" # inbound port on ovs_switch
            
            if "outbound" in data[name]:
                config[name]["outbound"] = str(data[name]["outbound"]) # outbound physical interface
                config[name]["outbound_mac"] =  str(data[name]["outbound_mac"]) # otbound mac address
                config[name]["outbound_port"] = "" # outbound port on ovs_switch

            config[name]["cpu"] = str(data[name]["cpu"]) # given number of CPUs
            config[name]["mem"] = str(data[name]["mem"]) # given mem size

            config[name]["mgmt_ip"] = str(data[name]["mgmt_ip"]) # mgmt IP address

            config[name]["start"] = str(data[name]["start"]) # application start script
            config[name]["stop"] = str(data[name]["stop"]) # application stop script

            if "stat" in data[name]:
                config[name]["stat"] = str(data[name]["stat"]) # application stat script (for passive VNFs)
            else:
                config[name]["stat"] = ""

            if "init" in data[name]:
                config[name]["init"] = str(data[name]["init"]) # VNF init script before/without NAT
            else:
                config[name]["init"] = ""

            if "nat_init" in data[name]:
                config[name]["nat_init"] = str(data[name]["nat_init"]) # VNF init script after NAT
            else:
                config[name]["nat_init"] = ""

    return config

def update_VNF_configurations(config):
    
    config["firewall"]["inbound"] = "75"
    config["firewall"]["outbound"] = "76"
    config["netsniff-ng"]["inbound"] = "49"
    config["netsniff-ng"]["outbound"] = ""
    config["snort-ids"]["inbound"] = "51"
    config["snort-ids"]["outbound"] = ""
    config["suricata-ids"]["inbound"] = "52"
    config["suricata-ids"]["outbound"] = ""
    config["suricata-ips"]["inbound"] ="53"
    config["suricata-ips"]["outbound"] ="54"

    config["tcpdump"]["inbound"] = "56"
    config["tcpdump"]["outbound"] = ""    
    for process in psutil.process_iter():
        try:
            vnf = process.as_dict(attrs=['name', 'pid', 'cmdline'])
        except psutil.NoSuchProcess:
            pass

        if vnf['name'] != "kvm":
            continue
        for entry in vnf['cmdline']:
            name = vnf['cmdline'][vnf['cmdline'].index('-name') + 1]
            if name not in config:
                #print("%s is not in the VNF configurations" % (name))
                continue

            config[name]["pid"] = vnf['pid']
    '''       
            mac = config[name]["inbound_mac"] # added to config file for each vnf
            cmd = "ovs-appctl fdb/show vmbr0 | grep " + mac + " | awk '{print $1}'"
            res = subprocess.check_output(cmd, shell=True)
            port = res.rstrip()
            config[name]["inbound_port"] = port

            if "outbound_mac" in config[name]:
                mac = config[name]["outbound_mac"] # added to config file for each vnf
                cmd = "ovs-appctl fdb/show vmbr0 | grep " + mac + " | awk '{print $1}'"
                res = subprocess.check_output(cmd, shell=True)
                port = res.rstrip()
                config[name]["outbound_port"] = port

    '''
    return config

def get_extras():
    extras = []

    for process in psutil.process_iter():
        try:
            p = process.as_dict(attrs=['name', 'pid'])
        except psutil.NoSuchProcess:
            pass

        if "ovs-vswitchd" in p["name"]: # software switch
            extras.append(p)
        elif "vhost-" in p["name"]: # virtual interface queue
            extras.append(p)

    return extras

def get_list_of_VNFs(config):
    VNFs = []

    for name in config:
        VNFs.append(config[name]["name"])

    return VNFs

def make_resources_VNFs(analysis, config, VNFs, flag):
    cpu_list = analysis["cpu"].split(',')
    mem_list = analysis["mem"].split(',')

    cpus = []
    count = pow(len(cpu_list), len(VNFs))

    for cnt in range(count):
        cpu_base = []
        for vnf in VNFs:
            cpu_base.append(0)
        cpus.append(cpu_base)

    for idx in range(len(VNFs)):
        cpus_idx = 0
        while cpus_idx < count:
            for cpu in cpu_list:
                loop_cnt = pow(len(cpu_list), len(VNFs) - idx - 1)
                for loop in range(loop_cnt):
                    if flag == False:
                        cpus[cpus_idx][idx] = cpu
                    else:
                        vnf_cpu = config[VNFs[idx]]["cpu"].split(',')
                        if cpu in vnf_cpu:
                            cpus[cpus_idx][idx] = cpu
                    cpus_idx += 1

    final_cpus = []
    for cpu in cpus:
        if cpu not in final_cpus and 0 not in cpu:
            final_cpus.append(cpu)

    mems = []
    count = pow(len(mem_list), len(VNFs))

    for cnt in range(count):
        mem_base = []
        for vnf in VNFs:
            mem_base.append(0)
        mems.append(mem_base)

    for idx in range(len(VNFs)):
        mems_idx = 0
        while mems_idx < count:
            for mem in mem_list:
                loop_cnt = pow(len(mem_list), len(VNFs) - idx - 1)
                for loop in range(loop_cnt):
                    if flag == False:
                        mems[mems_idx][idx] = mem
                    else:
                        vnf_mem = config[VNFs[idx]]["mem"].split(',')
                        if mem in vnf_mem:
                            mems[mems_idx][idx] = mem
                    mems_idx += 1

    final_mems = []
    for mem in mems:
        if mem not in final_mems and 0 not in mem:
            final_mems.append(mem)

    return final_cpus, final_mems

def get_cpuset_of_VNFs(cpu, VNFs):
    cpuset = []

    cpu_list = []
    for v in cpu:
        cpu_list.append(int(v))

    total_cpus = int(os.sysconf('SC_NPROCESSORS_ONLN'))
    required_cpus = sum(cpu_list)

    for idx in range(len(cpu_list)):
        assigned_cpus = 0

        if idx == 0:
            assigned_cpus = 0
        else:
            for prev in range(len(cpu_list)):
                if prev < idx:
                    assigned_cpus += cpu_list[prev]
                else:
                    break

        if cpu_list[idx] == 1:
            start = assigned_cpus % total_cpus
            cpu_range = "%s" % (start)
            cpuset.append(cpu_range)
        else:
            start = assigned_cpus % total_cpus
            end = (assigned_cpus + int(cpu[idx]) - 1) % total_cpus
            if start < end:
                cpu_range = "%d-%d" % (start, end)
            else:
                cpu_range = "%d-%d,0-%d" % (start, total_cpus-1, end)
            cpuset.append(cpu_range)

    return cpuset

def set_cpus_of_VNFs(cpu, cpuset, VNFs):
    for idx in range(len(VNFs)):
        os.system("util/set-vcpu.sh %s %s %s" % (VNFs[idx], cpuset[idx], cpu[idx]))
        print ("set-vcpu " + VNFs[idx] + " " + cpuset[idx] + " " + cpu[idx])

    return

def set_mems_of_VNFs(mem, VNFs):
    for idx in range(len(VNFs)):
        size = str(int(mem[idx]) * 1024)
        os.system("util/set-vmem.sh %s %s" % (VNFs[idx], size))
        print ("set-vmem " + VNFs[idx] + " " + size)

    return

def is_VNF_alive(mgmt_ip):
    res = os.system("ssh " + mgmt_ip + " exit 2> /dev/null")
    if res == 0:
        return True
    else:
        return False

def is_VNF_active(vnf):
    print (type(vnf))
    return proxmoxx.check_status(vnf);

def power_on_VNFs(config, VNFs):
    for vnf in VNFs:
        if is_VNF_active(vnf) == False:
            proxmoxx.startvm(config[vnf]["vmid"])
            #proxmoxx.startvm(vnf_dict[vnf])
            #curr = conn.lookupByName(vnf)
            #curr.create()
            #conn.close()
        else: # True
            #curr = conn.lookupByName(vnf)
            #curr.destroy()
            proxmoxx.stopvm(config[vnf]["vmid"])
            #proxmoxx.stopvm(config[vnf]["vmid"])
            time.sleep(1.0)
            proxmoxx.startvm(config[vnf]["vmid"])
            #proxmoxx.startvm(vnf_dict[vnf])

    for vnf in VNFs:
        power_on = False
        while power_on == False:
            if is_VNF_alive(config[vnf]["mgmt_ip"]):
                power_on = True

    return

def shut_down_VNFs(config, VNFs):
    filtered = []

    for vnf in VNFs:
        ret = is_VNF_active(vnf)

        if ret > 0:
            proxmoxx.stopvm(config[vnf]["vmid"])
            #proxmoxx.stopvm(vnf_dict[vnf])
        if ret >= 0:
            filtered.append(vnf)

    return filtered

def is_after_NAT(vnf, VNFs):
    ret = False

    for v in VNFs:
        if v == "NAT":
            ret = True
        elif v == vnf:
            break

    return ret

def start_applications_in_VNFs(config, VNFs):
    for vnf in VNFs:
        if is_after_NAT(vnf, VNFs):
            os.system("ssh " + config[vnf]["mgmt_ip"] + " " + config[vnf]["start"] + " " + config[vnf]["nat_init"])
        else:
            os.system("ssh " + config[vnf]["mgmt_ip"] + " " + config[vnf]["start"] + " " + config[vnf]["init"])
            print ("ssh " + config[vnf]["mgmt_ip"] + " " + config[vnf]["start"] + " " + config[vnf]["init"])

    return

def stop_applications_in_VNFs(config, VNFs):
    for vnf in VNFs:
        os.system("ssh " + config[vnf]["mgmt_ip"] + " " + config[vnf]["stop"])

    return

def get_application_stats_of_VNFs(config, VNFs):
    for vnf in VNFs:
        if config[vnf]["type"] == "passive":
            os.system("ssh " + config[vnf]["mgmt_ip"] + " sudo " + config[vnf]["stat"] + " | tee tmp/stats.log")

            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            f = open("tmp/stats.log", "r")

            lines = f.read().splitlines()

            for line in lines:
                column = line.split()
                database.add_stats(timestamp, VNFs, vnf, float(column[0]), float(column[1]), float(column[2]))

            f.close()

            os.system("rm tmp/stats.log")
        else:
            print ("passed " + vnf)

    return

def make_chain_of_VNFs(config, VNFs):
    os.system("sudo ovs-ofctl del-flows vmbr0")
    ''' 
    os.system("sudo ovs-ofctl add-flow vmbr0 in_port=11,actions=output:LOCAL")
    os.system("sudo ovs-ofctl add-flow vmbr0 in_port=LOCAL,actions=output:11")

    os.system("sudo ovs-ofctl add-flow vmbr0 in_port=13,actions=output:LOCAL")
    os.system("sudo ovs-ofctl add-flow vmbr0 in_port=LOCAL,actions=output:13")    
   
    '''
    rules = []
    
    vnf_cnt = 0
    out_port = ""

    rule = "sudo ovs-ofctl add-flow vmbr0 in_port=10,actions="

    for vnf in VNFs:
        output = config[vnf]["inbound"]
        print("output = ",output)

        if config[vnf]["type"] == "inline":
            out_port = config[vnf]["outbound"]
            print("out_port = ",out_port)
        
        if config[vnf]["type"] == "inline":
            if vnf_cnt == 0:
                print("OUTPUT = ", output)
                print(type(output))
                rule = rule + "output:" + output
            else:
                rule = rule + ",output:" + output

            vnf_cnt = 0
            rule = rule + ",output:LOCAL"
            print("RULE = ", rule)
            rules.append(rule)

            rule = "sudo ovs-ofctl add-flow vmbr0 in_port=" + out_port + ",actions="
        else: # passive
            if vnf_cnt == 0:
                rule = rule + "output:" + output
            else:
                rule = rule + ",output:" + output

            vnf_cnt = vnf_cnt + 1

    if vnf_cnt == 0:
        rule = rule + "output:12"
    else:
        rule = rule + ",output:12"

    rule = rule + ",output:LOCAL"
    print("RULE out = ", rule)
    rules.append(rule)

    rule = "sudo ovs-ofctl add-flow vmbr0 in_port=12,actions="    
    rev = []

    for vnf in VNFs:
        rev.append(vnf)

    rev.reverse()

    vnf_cnt = 0
    out_port = ""

    for vnf in rev:
        if config[vnf]["type"] == "inline":
            output = config[vnf]["outbound"]
        else:
            output = config[vnf]["inbound"]

        if config[vnf]["type"] == "inline":
            out_port = config[vnf]["inbound"]

        if config[vnf]["type"] == "inline":
            if vnf_cnt == 0:
                rule = rule + "output:" + output
            else:
                rule = rule + ",output:" + output

            vnf_cnt = 0
            rule = rule + ",output:LOCAL"
            rules.append(rule)

            rule = "sudo ovs-ofctl add-flow vmbr0 in_port=" + out_port + ",actions="
        else: # passive
            if vnf_cnt == 0:
                rule = rule + "output:" + output
            else:
                rule = rule + ",output:" + output

            vnf_cnt = vnf_cnt + 1

    if vnf_cnt == 0:
        rule = rule + "output:10"
    else:
        rule = rule + ",output:10"
    rule = rule + ",output:LOCAL"
    print("RULE last = ", rule)
    rules.append(rule)
    rules.append("sudo ovs-ofctl add-flow vmbr0 in_port=LOCAL,actions=output:12,output:10") #,output:" + str(config[vnf]["inbound"]))
    return rules

def initialize_Open_vSwitch(analysis):
    os.system("sudo ovs-ofctl del-flows vmbr0")
    os.system("sudo ovs-ofctl add-flow vmbr0 action=normal")
    return

def apply_chain_of_VNFs(rules):
    for rule in rules:
        os.system(rule)

    os.system("util/dump-flows.sh")

    return
