# General libraries
import os, time, threading
from datetime import datetime

# Probius libraries
import trace
import monitor
import vnf_mgmt
import database
from common import no_workload

def start_sender(g_config, VNFs, protocol, bandwidth):
    if no_workload == True:
        return

    option = " "

    if "NAT" in VNFs:
        print "Destination IP: " + g_config["local_receiver_nat_ip"]
        option = option + g_config["local_receiver_nat_ip"]
    else:
        print "Destination IP: " + g_config["local_receiver_ip"]
        option = option + g_config["local_receiver_ip"]

    if protocol == "udp":
        option = option + " -u "

    option = option + " -P " + g_config["sessions"]
    option = option + " -b " + str(int(bandwidth) / int(g_config["sessions"])) + "M " # Mbits/s per session

    if "NAT" in VNFs:
        os.system("ssh " + g_config["sender"] + " " + g_config["run_sender"] + " NAT " + option)
    else:
        os.system("ssh " + g_config["sender"] + " " + g_config["run_sender"] + " " + option)

    return

def stop_sender(g_config, VNFs):
    if no_workload == True:
        return

    if "NAT" in VNFs:
        os.system("ssh " + g_config["sender"] + " " + g_config["stop_sender"] + " NAT")
    else:
        os.system("ssh " + g_config["sender"] + " " + g_config["stop_sender"])

    return

def start_receiver(g_config, VNFs):
    if no_workload == True:
        return

    if "NAT" in VNFs:
        os.system("ssh " + g_config["receiver"] + " " + g_config["run_receiver"] + " NAT")
    else:
        os.system("ssh " + g_config["receiver"] + " " + g_config["run_receiver"])

    return

def stop_receiver(g_config, VNFs):
    if no_workload == True:
        return

    if "NAT" in VNFs:
        os.system("ssh " + g_config["receiver"] + " " + g_config["stop_receiver"] + " NAT")
    else:
        os.system("ssh " + g_config["receiver"] + " " + g_config["stop_receiver"])

    return

def stop_sender_and_receiver(g_config, VNFs):
    if no_workload == True:
        return

    if "NAT" in VNFs:
        os.system("ssh " + g_config["sender"] + " " + g_config["stop_sender"] + " NAT")
        os.system("ssh " + g_config["receiver"] + " " + g_config["stop_receiver"] + " NAT")
    else:
        os.system("ssh " + g_config["sender"] + " " + g_config["stop_sender"])
        os.system("ssh " + g_config["receiver"] + " " + g_config["stop_receiver"])

    return

def measure_latency(g_config, VNFs, flag):
    if no_workload == True:
        return

    LATENCY_LOG = "tmp/latency"

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if "NAT" in VNFs:
        os.system("ssh " + g_config["sender"] + " ping -c 1 " + g_config["local_receiver_nat_ip"] + " > /dev/null")
    else:
        os.system("ssh " + g_config["sender"] + " ping -c 1 " + g_config["local_receiver_ip"] + " > /dev/null")

    if "NAT" in VNFs:
        os.system("ssh " + g_config["sender"] + " " + g_config["measure_latency"] + " " + g_config["local_receiver_nat_ip"] + \
                  " | tee " + LATENCY_LOG)
    else:
        os.system("ssh " + g_config["sender"] + " " + g_config["measure_latency"] + " " + g_config["local_receiver_ip"] + \
                  " | tee " + LATENCY_LOG)

    f = open(LATENCY_LOG, "r")
    raw_data = f.read().splitlines()
    f.close()

    for data in raw_data:
        temp = data.split()

        if len(temp) >= 8:
            if flag == False: # without background traffic
                database.add_latency(timestamp, VNFs, "wo", temp[7])
            else: # with background traffic
                database.add_latency(timestamp, VNFs, "wt", temp[7])

    os.system("rm " + LATENCY_LOG)
       
    return

def send_workloads(g_config, config, VNFs, flag):
    monitor_time = int(g_config["monitor_time"])
    trace_time = int(g_config["trace_time"])

    protocols = g_config["protocol"].split(",")
    bandwidths = g_config["bandwidth"].split(",")

    for protocol in protocols: # TCP, UDP
        for bandwidth in bandwidths: # 200, 400, 600, 800, 1000 Mbits/s
            stop_sender_and_receiver(g_config, VNFs)
            print "Stopped the previous sender and receiver just in case"

            # ============ #

            vnf_mgmt.initialize_Open_vSwitch(g_config)
            print "Initialized Open vSwitch"

            vnf_mgmt.power_on_VNFs(config, VNFs)
            print "Powered on VNFs"

            config = vnf_mgmt.update_VNF_configurations(config)
            print "Updated VNF configurations"

            vnf_mgmt.start_applications_in_VNFs(config, VNFs)
            print "Executed applications in VNFs"

            rules = vnf_mgmt.make_chain_of_VNFs(config, VNFs)
            print "Made flow rules for the chain of VNFs"

            vnf_mgmt.apply_chain_of_VNFs(rules)
            print "Applied the chain of VNFs"

            # ============ #

            extras = vnf_mgmt.get_extras()
            print "Got the information of extra processes"

            monitor.initialize_VNF_statistics(VNFs, extras)
            print "Initialized VNF statistics"

            start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print "Protocol=%s, bandwidth=%sMB" % (protocol, bandwidth)

            time.sleep(1.0)

            start_receiver(g_config, VNFs)
            print "Executed a receiver"

            measure_latency(g_config, VNFs, False)
            print "Measured end-to-end latencies without workloads"

            start_sender(g_config, VNFs, protocol, bandwidth)
            print "Executed a sender (protocol=%s, bandwidth=%sMB)" % (protocol, bandwidth)

            time.sleep(5.0)
            print "Started to monitor VNFs"

            measure_latency(g_config, VNFs, True)
            print "Measured end-to-end latencies with workloads"

            # ============ #

            monitor.monitor_VNFs(g_config, config, VNFs, extras, monitor_time)

            # ============ #

            while True: # waiting until all monitoring threads are terminated
                if threading.active_count() == 1:
                    break
                else:
                    time.sleep(1.0)
            print "Stopped monitoring VNFs"

            vnf_mgmt.get_application_stats_of_VNFs(config, VNFs)
            print "Got the statistics of passive VNFs"

            # ============ #

            if flag == True:
                trace.run_trace(trace_time)
                print "Traced events"

                trace.analyze_trace(VNFs, protocol, bandwidth)
                print "Analyzed the events"

            # ============ #

            stop_sender(g_config, VNFs)
            print "Stopped the sender"

            stop_receiver(g_config, VNFs)
            print "Stopped the receiver"

            time.sleep(1.0)

            end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            database.add_testcase(VNFs, protocol, bandwidth, start_time, end_time)
            print "Logged the start and end points of a testcase"

            # ============ #

            vnf_mgmt.stop_applications_in_VNFs(config, VNFs)
            print "Terminated applications in VNFs"

            vnf_mgmt.shut_down_VNFs(VNFs)
            print "Shut down VNFs"

            # ============ #

    return
