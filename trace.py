# General libraries
import os, sys
import psutil
from datetime import datetime

# Probius libraries
import util
import database
from common import trace_log

tids = {}

def run_trace(trace_time):
    tids.clear()

    for process in psutil.process_iter():
        try:
            ps = process.as_dict(attrs=['name', 'pid'])
        except psutil.NoSuchProcess:
            pass

        if "kvm" not in ps["name"] and "vhost-" not in ps["name"]:
            continue

        p = psutil.Process(ps['pid'])
        threads = p.threads()
        for thread in threads:
            tid = thread[0]
            user_time = thread[1]
            system_time = thread[2]
            tids[str(tid)] = str(ps['pid'])

    events = "-e kvm:*"
    os.system("sudo trace-cmd record " + events + " sleep " + str(trace_time) + " > /dev/null")

    return

def analyze_trace(VNFs, protocol, bandwidth):
    os.system("sudo trace-cmd report -t 2> /dev/null > " + trace_log)

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    f = open(trace_log, "r")
    raw_traces = f.read().splitlines()

    num_cpus = 0
    empty_cpus = []

    traces = {}
    for raw_trace in raw_traces:
        #print("raw_trace", raw_trace)
        trace = raw_trace.split()
        #print("TRACE = ", trace)
        #print("TRACE 0 = ", trace[0])
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
            if "qemu-system-x86" not in trace[0] and not trace[0].startswith("kvm-"):
                continue

            cpu = int(trace[1][1:4])
            traces[cpu].append(trace)

    global_pairs = {}
    global_pairs_cnt = {}
    global_pairs_time = {}
    
    #print("TRACES = ",traces)
    #print("start cycle")
    for cpu in traces:
        #print("cpu", cpu)
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
            #print("event = ", event)

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
                #print("PAIRS= ", pair)
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

        #print("trace_info_cpu")
        #print(pairs)
        for pair in pairs:
            
            #print("pair = ", pair)
            #print("timestamp = ", timestamp)
            #print("cpu = ", cpu)
            database.trace_info_cpu(timestamp, cpu, pair, pairs_cnt[pair], pairs_time[pair])

    f.close()
    
    #print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    #print("trace_info_pid")
    for pid in global_pairs:
        for pair in global_pairs[pid]:
            #print("pair = ", pair)
            database.trace_info_pid(timestamp, pid, pair, global_pairs_cnt[pid][pair], global_pairs_time[pid][pair])

    os.system("rm " + trace_log)

    return
