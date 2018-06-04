#!/usr/bin/python

import os
import time
import threading
from datetime import datetime

import trace
import monitor
import vnf_mgmt
import database

def start_sender(analysis, VNFs, protocol, bandwidth):
    option = " "

    if "atto-vrouter-minimum-2-port-1" in VNFs or "NAT" in VNFs:
        print "Destination IP: " + analysis["local_receiver_nat_ip"]
        option = option + analysis["local_receiver_nat_ip"]
    else: # openstack or kvm
        print "Destination IP: " + analysis["local_receiver_ip"]
        option = option + analysis["local_receiver_ip"]

    if protocol == "udp":
        option = option + " -u "

    option = option + " -P " + analysis["sessions"]
    option = option + " -b " + str(int(bandwidth) / int(analysis["sessions"])) + "M " # Mbits/s per session

    if "atto-vrouter-minimum-2-port-1" in VNFs or "NAT" in VNFs:
        os.system("ssh " + analysis["sender"] + " " + analysis["run_sender"] + " NAT " + option)
    else: # openstack or kvm
        os.system("ssh " + analysis["sender"] + " " + analysis["run_sender"] + " " + option)

    return

def stop_sender(analysis, VNFs):
    if "atto-vrouter-minimum-2-port-1" in VNFs or "NAT" in VNFs:
        os.system("ssh " + analysis["sender"] + " " + analysis["stop_sender"] + " NAT")
    else: # openstack or kvm
        os.system("ssh " + analysis["sender"] + " " + analysis["stop_sender"])

    return

def start_receiver(analysis, VNFs):
    if "atto-vrouter-minimum-2-port-1" in VNFs or "NAT" in VNFs:
        os.system("ssh " + analysis["receiver"] + " " + analysis["run_receiver"] + " NAT")
    else: # openstack or kvm
        os.system("ssh " + analysis["receiver"] + " " + analysis["run_receiver"])

    return

def stop_receiver(analysis, VNFs):
    if "atto-vrouter-minimum-2-port-1" in VNFs or "NAT" in VNFs:
        os.system("ssh " + analysis["receiver"] + " " + analysis["stop_receiver"] + " NAT")
    else: # openstack or kvm
        os.system("ssh " + analysis["receiver"] + " " + analysis["stop_receiver"])

    return

def stop_sender_and_receiver(analysis, VNFs):
    if "atto-vrouter-minimum-2-port-1" in VNFs or "NAT" in VNFs:
        os.system("ssh " + analysis["sender"] + " " + analysis["stop_sender"] + " NAT")
        os.system("ssh " + analysis["receiver"] + " " + analysis["stop_receiver"] + " NAT")
    else: # openstack or kvm
        os.system("ssh " + analysis["sender"] + " " + analysis["stop_sender"])
        os.system("ssh " + analysis["receiver"] + " " + analysis["stop_receiver"])

    return

def measure_latency(analysis, VNFs, flag):
    LATENCY_LOG = "tmp/latency"

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if "atto-vrouter-minimum-2-port-1" in VNFs or "NAT" in VNFs:
        os.system("ssh " + analysis["sender"] + " ping -c 1 " + analysis["local_receiver_nat_ip"] + " > /dev/null")
    else: # openstack or kvm
        os.system("ssh " + analysis["sender"] + " ping -c 1 " + analysis["local_receiver_ip"] + " > /dev/null")

    if "atto-vrouter-minimum-2-port-1" in VNFs or "NAT" in VNFs:
        os.system("ssh " + analysis["sender"] + " " + analysis["measure_latency"] + " " + analysis["local_receiver_nat_ip"] + \
                  " | tee " + LATENCY_LOG)
    else: # openstack or kvm
        os.system("ssh " + analysis["sender"] + " " + analysis["measure_latency"] + " " + analysis["local_receiver_ip"] + \
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

def send_workloads(analysis, config, VNFs, flag):
    monitor_time = int(analysis["monitor_time"])
    trace_time = int(analysis["trace_time"])

    protocols = analysis["protocol"].split(",")
    bandwidths = analysis["bandwidth"].split(",")

    for protocol in protocols: # TCP, UDP
        for bandwidth in bandwidths: # 200, 400, 600, 800, 1000 Mbits/s
            stop_sender_and_receiver(analysis, VNFs)
            print "Stopped the previous sender and receiver just in case"

            # ============ #

            if vnf_mgmt.is_openstack_env() == False: # kvm
                vnf_mgmt.initialize_Open_vSwitch(analysis)
                print "Initialized Open vSwitch"

                vnf_mgmt.power_on_VNFs(config, VNFs)
                print "Powered on VNFs"

                config = vnf_mgmt.update_VNF_configurations(config)
                print "Updated VNF configurations"

                vnf_mgmt.start_applications_in_VNFs(config, VNFs)
                print "Executed applications in VNFs"

                rules = vnf_mgmt.make_the_chain_of_VNFs(config, VNFs)
                print "Made flow rules for the chain of VNFs"

                vnf_mgmt.apply_the_chain_of_VNFs(rules)
                print "Applied the chain of VNFs"

            # ============ #

            extras = vnf_mgmt.get_extras()
            print "Got the information of extra processes"

            monitor.initialize_VNF_statistics(VNFs, extras)
            print "Initialized VNF statistics"

            start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print "Protocol=%s, bandwidth=%sMB" % (protocol, bandwidth)

            time.sleep(1.0)

            start_receiver(analysis, VNFs)
            print "Executed a receiver"

            measure_latency(analysis, VNFs, False)
            print "Measured end-to-end latencies without workloads"

            start_sender(analysis, VNFs, protocol, bandwidth)
            print "Executed a sender (protocol=%s, bandwidth=%sMB)" % (protocol, bandwidth)

            time.sleep(5.0)
            print "Started to monitor VNFs"

            measure_latency(analysis, VNFs, True)
            print "Measured end-to-end latencies with workloads"

            monitor.monitor_VNFs(analysis, config, VNFs, extras, monitor_time)

            while True: # waiting until all monitoring threads are terminated
                if threading.active_count() == 1:
                    break
                else:
                    time.sleep(1.0)
            print "Stopped monitoring VNFs"

            if vnf_mgmt.is_athene_env() == False: # openstack or kvm
                vnf_mgmt.get_application_stats_of_VNFs(config, VNFs)
                print "Got the statistics of passive VNFs"

            if flag == True:
                trace.run_trace(trace_time)
                print "Traced events"

                trace.analyze_trace(VNFs, protocol, bandwidth)
                print "Analyzed the events"

            stop_sender(analysis, VNFs)
            print "Stopped the sender"

            stop_receiver(analysis, VNFs)
            print "Stopped the receiver"

            time.sleep(1.0)

            end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            database.add_testcase(VNFs, protocol, bandwidth, start_time, end_time)
            print "Logged the start and end points of a testcase"

            # ============ #

            if vnf_mgmt.is_openstack_env() == False: # kvm
                vnf_mgmt.stop_applications_in_VNFs(config, VNFs)
                print "Terminated applications in VNFs"

                vnf_mgmt.shut_down_VNFs(VNFs)
                print "Shut down VNFs"

            # ============ #

    return
