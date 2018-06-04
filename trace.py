#!/usr/bin/python

import os
import sys
import psutil
import database
from datetime import datetime

import util

TRACE_LOG = "tmp/trace.log"

tids = {}

def run_trace(trace_time):
    tids.clear()

    for process in psutil.process_iter():
        try:
            ps = process.as_dict(attrs=['name', 'pid'])
        except psutil.NoSuchProcess:
            pass

        accepted = False

        if "qemu-system-x86_64" in ps["name"]:
            accepted = True
        elif "qemu-kvm" in ps["name"]:
            accepted = True
        elif "vhost-" in ps["name"]:
            accepted = True

        if accepted == False:
            continue

        p = psutil.Process(ps['pid'])
        threads = p.get_threads()
        for thread in threads:
            tid, user_time, system_time = thread
            tids[str(tid)] = str(ps['pid'])

    events = "-e kvm:*"
    os.system("sudo trace-cmd record " + events + " sleep " + str(trace_time) + " > /dev/null")

    return

def analyze_trace(VNFs, protocol, bandwidth):
    os.system("sudo trace-cmd report -t 2> /dev/null > " + TRACE_LOG)

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    f = open(TRACE_LOG, "r")
    raw_traces = f.read().splitlines()

    num_cpus = 0
    empty_cpus = []

    traces = {}
    for raw_trace in raw_traces:
        trace = raw_trace.split()

        if trace[0] == "version":
            continue
        elif trace[0] == "CPU":
            empty_cpus.append(int(trace[1]))
            continue
        elif "cpus=" in trace[0]:
            cpus = trace[0].split("=")
            num_cpus = int(cpus[1])
            for cpu in range(num_cpus):
                if cpu not in empty_cpus:
                    traces[cpu] = []
            continue
        else:
            if "qemu-system-x86" not in trace[0] and "qemu-kvm" not in trace[0]:
                continue

            cpu = int(trace[1][1:4])
            traces[cpu].append(trace)

    global_pairs = {}
    global_pairs_cnt = {}
    global_pairs_time = {}

    for cpu in traces:
        pre_pid = ""
        pre_tid = ""
        pre_time = 0.0
        pre_event = ""
        pre_data = ""

        pairs = []
        pairs_cnt = {}
        pairs_time = {}

        total_cnt = 0
        total_time = 0.0

        for trace in traces[cpu]:
            tid = trace[0].split("-")[-1]

            pid = ""
            if tid in tids:
                pid = tids[tid]
            else:
                pid = "Unknown"

            cpu = trace[1][1:4]
            time = float(trace[2][3:-1])
            event = trace[3][0:-1]

            data = "N/A"
            if event == "kvm_ple_window":
                data = trace[5][0:-1]
            if event == "kvm_vcpu_wakeup":
                data = trace[4]
            elif event == "kvm_fpu":
                data = trace[4]
            elif event == "kvm_entry":
                data = trace[5]
            elif event == "kvm_exit":
                data = trace[5]
            elif event == "kvm_userspace_exit":
                data = trace[5]
            elif event == "kvm_msr":
                data = trace[5]
            elif event == "kvm_pio":
                data = trace[6]

            if pre_event != "":
                pair = "%s %s %s %s %s %s %s %s" % (pre_event, pre_pid, pre_tid, pre_data, event, pid, tid, data)

                if pair not in pairs:
                    pairs.append(pair)
                    pairs_cnt[pair] = 1
                    pairs_time[pair] = (time - pre_time)
                else:
                    pairs_cnt[pair] += 1
                    pairs_time[pair] += (time - pre_time)

                if pid not in global_pairs:
                    global_pairs[pid] = []
                    global_pairs_cnt[pid] = {}
                    global_pairs_time[pid] = {}

                if pair not in global_pairs[pid]:
                    global_pairs[pid].append(pair)
                    global_pairs_cnt[pid][pair] = 1
                    global_pairs_time[pid][pair] = (time - pre_time)
                else:
                    global_pairs_cnt[pid][pair] += 1
                    global_pairs_time[pid][pair] += (time - pre_time)

                total_cnt += 1
                total_time += (time - pre_time)

            pre_pid = pid
            pre_tid = tid
            pre_time = time
            pre_event = event
            pre_data = data

        for pair in pairs:
            database.trace_info_cpu(timestamp, cpu, pair, pairs_cnt[pair], pairs_time[pair])

    f.close()

    for pid in global_pairs:
        for pair in global_pairs[pid]:
            database.trace_info_pid(timestamp, pid, pair, global_pairs_cnt[pid][pair], global_pairs_time[pid][pair])

    os.system("rm " + TRACE_LOG)

    return
