import time
import sqlite3
import threading

import util
from common import analysis_database

lock = threading.Lock()
query_queue = []

def run_query(query, flag=False):
    global lock

    if flag == True:
        lock.acquire()

        conn = sqlite3.connect(analysis_database)
        c = conn.cursor()

        for queued in query_queue:
            c.execute(queued)
        del query_queue[:]

        c.execute(query)

        conn.commit()
        conn.close()

        lock.release()
    else:
        lock.acquire()
        query_queue.append(query)
        lock.release()

    return

def initialize_database():
    query = "CREATE TABLE IF NOT EXISTS testcase ( \
             testcase TEXT, protocol TEXT, bandwidth TEXT, start_time TEXT, end_time TEXT);"

    run_query(query)

    query = "CREATE TABLE IF NOT EXISTS latency ( \
             timestamp TEXT, testcase TEXT, workload TEXT, latency TEXT);"

    run_query(query)

    query = "CREATE TABLE IF NOT EXISTS stats ( \
             timestamp TEXT, testcase TEXT, vnf TEXT, packets TEXT, bytes TEXT, rate TEXT);"

    run_query(query)

    query = "CREATE TABLE IF NOT EXISTS guest_vnf_info ( \
             timestamp TEXT, vnf TEXT, cpu_num TEXT, \
             cpu_time TEXT, vcpu_time TEXT, user_time TEXT, system_time TEXT, total_mem TEXT, rss_mem TEXT, \
             read_count TEXT, read_bytes TEXT, write_count TEXT, write_bytes TEXT, \
             packets_recv TEXT, bytes_recv TEXT, packets_sent TEXT, bytes_sent TEXT);"

    run_query(query)

    query = "CREATE TABLE IF NOT EXISTS host_vnf_info ( \
             timestamp TEXT, vnf TEXT, pid TEXT, cpu_num TEXT, cpu_affinity TEXT, \
             cpu_percent TEXT, user_time TEXT, system_time TEXT, \
             mem_percent TEXT, total_mem TEXT, rss_mem TEXT, \
             read_count TEXT, read_bytes TEXT, write_count TEXT, write_bytes TEXT, \
             num_threads TEXT, vol_ctx TEXT, invol_ctx TEXT);"

    run_query(query)

    query = "CREATE TABLE IF NOT EXISTS host_ext_info ( \
             timestamp TEXT, name TEXT, pid TEXT, cpu_num TEXT, cpu_affinity TEXT, \
             cpu_percent TEXT, user_time TEXT, system_time TEXT, mem_percent TEXT, \
             read_count TEXT, read_bytes TEXT, write_count TEXT, write_bytes TEXT, \
             num_threads TEXT, vol_ctx TEXT, invol_ctx TEXT);"

    run_query(query)

    query = "CREATE TABLE IF NOT EXISTS host_info ( \
             timestamp TEXT, \
             cpu_percent TEXT, user_time TEXT, nice_time TEXT, system_time TEXT, \
             idle_time TEXT, iowait_time TEXT, irq_time TEXT, softirq_time TEXT, \
             steal_time TEXT, guest_time TEXT, guest_nice_time TEXT, \
             mem_percent TEXT, total_mem TEXT, available_mem TEXT, used_mem TEXT, free_mem TEXT, \
             active_mem TEXT, inactive_mem TEXT, buffers_mem TEXT, cached_mem TEXT, \
             read_count TEXT, read_bytes TEXT, write_count TEXT, write_bytes TEXT);"

    run_query(query)

    query = "CREATE TABLE IF NOT EXISTS host_net ( \
             timestamp TEXT, interface TEXT, packets_recv TEXT, bytes_recv TEXT, packets_sent TEXT, bytes_sent TEXT);"

    run_query(query)

    query = "CREATE TABLE IF NOT EXISTS trace_info_cpu ( \
             timestamp TEXT, cpu TEXT, \
             pre_event TEXT, pre_pid TEXT, pre_tid TEXT, pre_data TEXT, \
             curr_event TEXT, curr_pid TEXT, curr_tid TEXT, curr_data TEXT, \
             count TEXT, time TEXT);"

    run_query(query)

    query = "CREATE TABLE IF NOT EXISTS trace_info_pid ( \
             timestamp TEXT, pid TEXT, \
             pre_event TEXT, pre_pid TEXT, pre_tid TEXT, pre_data TEXT, \
             curr_event TEXT, curr_pid TEXT, curr_tid TEXT, curr_data TEXT, \
             count TEXT, time TEXT);"

    run_query(query)

    query = "CREATE TABLE IF NOT EXISTS vnf_stats ( \
             testcase TEXT, protocol TEXT, bandwidth TEXT, latency TEXT, vnf TEXT, \
             g_cpu_time TEXT, g_vcpu_time TEXT, g_user_time TEXT, g_system_time TEXT, \
             h_cpu_percent TEXT, h_user_time TEXT, h_system_time TEXT, \
             h_mem_percent TEXT, h_total_mem TEXT, h_rss_mem TEXT, \
             g_read_count TEXT, g_read_bytes TEXT, g_write_count TEXT, g_write_bytes TEXT, \
             pps_recv TEXT, bps_recv TEXT, pps_sent TEXT, bps_sent TEXT, \
             h_num_threads TEXT, h_vol_ctx TEXT, h_invol_ctx TEXT);"

    run_query(query)

    return

def add_testcase(VNFs, protocol, bandwidth, start_time, end_time):
    testcase = ""
    for vnf in VNFs:
        if testcase == "":
            testcase = vnf
        else:
            testcase = testcase + "," + vnf

    query = "insert into testcase (testcase, protocol, bandwidth, start_time, end_time) \
             values ('%s', '%s', '%s', '%s', '%s');" \
            % (testcase, protocol, bandwidth, start_time, end_time)

    run_query(query, True)

    return

def add_latency(timestamp, VNFs, workload, latency):
    testcase = ""
    for vnf in VNFs:
        if testcase == "":
            testcase = vnf
        else:
            testcase = testcase + "," + vnf

    query = "insert into latency (timestamp, testcase, workload, latency) values ('%s', '%s', '%s', '%s');" \
             % (timestamp, testcase, workload, latency)

    run_query(query)

    return

def add_stats(timestamp, VNFs, vnf, packet, byte, rate):
    testcase = ""
    for v in VNFs:
        if testcase == "":
            testcase = v
        else:
            testcase = testcase + "," + v

    query = "insert into stats (timestamp, testcase, vnf, packets, bytes, rate) values ('%s', '%s', '%s', '%f', '%f', '%f');" \
             % (timestamp, testcase, vnf, packet, byte, rate)

    run_query(query)

    return

def guest_vnf_info(vnf, timestamp, vnf_stats):
    query = "insert into guest_vnf_info (timestamp, vnf, \
             cpu_num, cpu_time, vcpu_time, user_time, system_time, total_mem, rss_mem, \
             read_count, read_bytes, write_count, write_bytes, \
             packets_recv, bytes_recv, packets_sent, bytes_sent) \
             values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s');" \
            % (timestamp, vnf, vnf_stats["cpu_num"], \
               vnf_stats["cpu_time"], vnf_stats['vcpu_time'], vnf_stats["user_time"], vnf_stats["system_time"], \
               vnf_stats["total_mem"], vnf_stats["rss_mem"], \
               vnf_stats["read_count"], vnf_stats["read_bytes"], vnf_stats["write_count"], vnf_stats["write_bytes"], \
               vnf_stats["packets_recv"], vnf_stats["bytes_recv"], vnf_stats["packets_sent"], vnf_stats["bytes_sent"])

    run_query(query)

    return

def host_VNF_info(vnf, timestamp, vnf_stats):
    query = "insert into host_vnf_info (timestamp, vnf, pid, cpu_num, cpu_affinity, \
             cpu_percent, user_time, system_time, mem_percent, total_mem, rss_mem, \
             read_count, read_bytes, write_count, write_bytes, num_threads, vol_ctx, invol_ctx) \
             values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', \
                     '%s', '%s', '%s', '%s', '%s', '%s', '%s');" \
            % (timestamp, vnf, vnf_stats["pid"], vnf_stats["cpu_num"], vnf_stats["cpu_affinity"], \
               vnf_stats["cpu_percent"], vnf_stats["user_time"], vnf_stats["system_time"], \
               vnf_stats["mem_percent"], vnf_stats['total_mem'], vnf_stats["rss_mem"], \
               vnf_stats["read_count"], vnf_stats["read_bytes"], vnf_stats["write_count"], vnf_stats["write_bytes"], \
               vnf_stats["num_threads"], vnf_stats["vol_ctx"], vnf_stats["invol_ctx"])

    run_query(query)

    return

def host_ext_info(timestamp, ext_stats):
    query = "insert into host_ext_info (timestamp, name, pid, cpu_num, cpu_affinity, \
             cpu_percent, user_time, system_time, mem_percent, \
             read_count, read_bytes, write_count, write_bytes, num_threads, vol_ctx, invol_ctx) \
             values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', \
                     '%s', '%s', '%s', '%s', '%s', '%s', '%s');" \
            % (timestamp, ext_stats["name"], ext_stats["pid"], ext_stats["cpu_num"], ext_stats["cpu_affinity"], \
               ext_stats["cpu_percent"], ext_stats["user_time"], ext_stats["system_time"], ext_stats["mem_percent"], \
               ext_stats["read_count"], ext_stats["read_bytes"], ext_stats["write_count"], ext_stats["write_bytes"], \
               ext_stats["num_threads"], ext_stats["vol_ctx"], ext_stats["invol_ctx"])

    run_query(query)

    return

def host_info(timestamp, host_stats):
    query = "insert into host_info \
             (timestamp, cpu_percent, user_time, nice_time, system_time, idle_time, iowait_time, \
             irq_time, softirq_time, steal_time, guest_time, guest_nice_time, mem_percent, total_mem, available_mem, used_mem, \
             free_mem, active_mem, inactive_mem, buffers_mem, cached_mem, \
             read_count, read_bytes, write_count, write_bytes) \
             values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', \
                     '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', \
                     '%s', '%s', '%s');" \
            % (timestamp, host_stats["cpu_percent"], host_stats["user_time"], host_stats["nice_time"], \
               host_stats["system_time"], host_stats["idle_time"], host_stats["iowait_time"], \
               host_stats["irq_time"], host_stats["softirq_time"], host_stats["steal_time"], \
               host_stats["guest_time"], host_stats["guest_nice_time"], \
               host_stats["mem_percent"], host_stats["total_mem"], host_stats["available_mem"], host_stats["used_mem"], \
               host_stats["free_mem"], host_stats["active_mem"], host_stats["inactive_mem"], \
               host_stats["buffers_mem"], host_stats["cached_mem"], \
               host_stats["read_count"], host_stats["read_bytes"], host_stats["write_count"], host_stats["write_bytes"])

    run_query(query)

    return

def host_net(timestamp, host_nets):
    query = "insert into host_net \
             (timestamp, interface, packets_recv, bytes_recv, packets_sent, bytes_sent) \
             values ('%s', '%s', '%s', '%s', '%s', '%s');" \
            % (timestamp, host_nets["interface"], \
               host_nets["packets_recv"], host_nets["bytes_recv"], host_nets["packets_sent"], host_nets["bytes_sent"])

    run_query(query)

    return

def trace_info_cpu(timestamp, cpu, pair, count, time):
    trace = pair.split(" ")

    pre_event = trace[0]
    pre_pid = trace[1]
    pre_tid = trace[2]
    pre_data = trace[3]

    curr_event = trace[4]
    curr_pid = trace[5]
    curr_tid = trace[6]
    curr_data = trace[7]

    query = "insert into trace_info_cpu (timestamp, cpu, pre_event, pre_pid, pre_tid, pre_data, \
                                         curr_event, curr_pid, curr_tid, curr_data, count, time) \
             values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%d', '%.9f');" \
             % (timestamp, cpu, pre_event, pre_pid, pre_tid, pre_data, curr_event, curr_pid, curr_tid, curr_data, count, time)

    run_query(query)

    return

def trace_info_pid(timestamp, pid, pair, count, time):
    trace = pair.split(" ")

    pre_event = trace[0]
    pre_pid = trace[1]
    pre_tid = trace[2]
    pre_data = trace[3]

    curr_event = trace[4]
    curr_pid = trace[5]
    curr_tid = trace[6]
    curr_data = trace[7]

    query = "insert into trace_info_pid (timestamp, pid, pre_event, pre_pid, pre_tid, pre_data, \
                                         curr_event, curr_pid, curr_tid, curr_data, count, time) \
             values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%d', '%.9f');" \
             % (timestamp, pid, pre_event, pre_pid, pre_tid, pre_data, curr_event, curr_pid, curr_tid, curr_data, count, time)

    run_query(query)

    return

def add_vnf_stats(stats):
    query = "insert into vnf_stats \
             (testcase, protocol, bandwidth, latency, vnf, \
              g_cpu_time, g_vcpu_time, g_user_time, g_system_time, h_cpu_percent, h_user_time, h_system_time, \
              h_mem_percent, h_total_mem, h_rss_mem, g_read_count, g_read_bytes, g_write_count, g_write_bytes, \
              pps_recv, bps_recv, pps_sent, bps_sent, h_num_threads, h_vol_ctx, h_invol_ctx) \
              values ('%s', '%s', '%s', '%.3f', '%s', '%.9f', '%.9f', '%.9f', '%.9f', \
                      '%.2f', '%.9f', '%.9f', '%.2f', '%.2f', '%.2f', \
                      '%.2f', '%.2f', '%.2f', '%.2f', '%.2f', '%.2f', '%.2f', '%.2f', '%.2f', '%.2f', '%.2f');" \
             % (stats["testcase"], stats["protocol"], stats["bandwidth"], stats["latency"], stats["vnf"], \
                stats["g_cpu_time"], stats["g_vcpu_time"], stats["g_user_time"], stats["g_system_time"], \
                stats["h_cpu_percent"], stats["h_user_time"], stats["h_system_time"], \
                stats["h_mem_percent"], stats["h_total_mem"], stats["h_rss_mem"], \
                stats["g_read_count"], stats["g_read_bytes"], stats["g_write_count"], stats["g_write_bytes"], \
                stats["pps_recv"], stats["bps_recv"], stats["pps_sent"], stats["bps_sent"], \
                stats["h_num_threads"], stats["h_vol_ctx"], stats["h_invol_ctx"])

    run_query(query, True)

    return

def update_vnf_stats(config):
    conn = sqlite3.connect(analysis_database)

    cur = conn.cursor()
    cur.execute("select * from testcase order by start_time")
    testcases = cur.fetchall()

    for testcase in testcases:
        case = testcase[0]
        protocol = testcase[1]
        bandwidth = testcase[2]
        start_time = testcase[3]
        end_time = testcase[4]

        cpu_nums = {}
        cur.execute("select distinct vnf, cpu_num from guest_vnf_info where \
                     timestamp >= '" + start_time + "' and timestamp <= '" + end_time + "'")
        vnf_cpu_nums = cur.fetchall()
        for vnf_cpu_num in vnf_cpu_nums:
            vnf = vnf_cpu_num[0]
            cpu_num = vnf_cpu_num[1]
            cpu_nums[vnf] = cpu_num

        VNFs = ""
        for vnf in case.split(","):
            if VNFs == "":
                VNFs += "%s(%s)" % (vnf, cpu_nums[vnf])
            else:
                VNFs += ",%s(%s)" % (vnf, cpu_nums[vnf])

        cur.execute("select latency from latency where workload = 'wo' and \
                     timestamp >= '" + start_time + "' and timestamp <= '" + end_time + "'")
        latencies = cur.fetchall()
        latency = util.get_latency(latencies)

        for vnf in case.split(","):
            vnf_stats = {}

            vnf_stats["testcase"] = VNFs

            vnf_stats["protocol"] = protocol
            vnf_stats["bandwidth"] = bandwidth

            vnf_stats["latency"] = latency

            vnf_stats["vnf"] = vnf

            cur.execute("select cpu_time, vcpu_time, user_time, system_time \
                         from guest_vnf_info where vnf = '" + vnf + "' and \
                         timestamp >= '"+start_time+"' and timestamp <= '"+end_time+"'")
            guest_cpu_times = cur.fetchall()
            g_cpu_time, g_vcpu_time, g_user_time, g_system_time = \
                util.get_guest_cpu_time(guest_cpu_times)

            vnf_stats["g_cpu_time"] = g_cpu_time
            vnf_stats["g_vcpu_time"] = g_vcpu_time
            vnf_stats["g_user_time"] = g_user_time
            vnf_stats["g_system_time"] = g_system_time

            cur.execute("select cpu_percent, user_time, system_time \
                         from host_vnf_info where vnf = '" + vnf + "' and \
                         timestamp >= '"+start_time+"' and timestamp <= '"+end_time+"'")
            host_cpu_times = cur.fetchall()
            h_cpu_percent, h_user_time, h_system_time = \
               util.get_host_cpu_time(host_cpu_times)

            vnf_stats["h_cpu_percent"] = h_cpu_percent
            vnf_stats["h_user_time"] = h_user_time
            vnf_stats["h_system_time"] = h_system_time

            cur.execute("select mem_percent, total_mem, rss_mem \
                         from host_vnf_info where vnf = '" + vnf + "' and \
                         timestamp >= '"+start_time+"' and timestamp <= '"+end_time+"'")
            host_mem_usages = cur.fetchall()
            h_mem_percent, h_total_mem, h_rss_mem = util.get_mem_usage(host_mem_usages)

            vnf_stats["h_mem_percent"] = h_mem_percent
            vnf_stats["h_total_mem"] = h_total_mem
            vnf_stats["h_rss_mem"] = h_rss_mem

            cur.execute("select read_count, read_bytes, write_count, write_bytes \
                         from guest_vnf_info where vnf = '" + vnf + "' and \
                         timestamp >= '"+start_time+"' and timestamp <= '"+end_time+"'")
            guest_io_counters = cur.fetchall()
            g_read_count, g_read_bytes, g_write_count, g_write_bytes = \
                util.get_io_counters(guest_io_counters)

            vnf_stats["g_read_count"] = g_read_count
            vnf_stats["g_read_bytes"] = g_read_bytes
            vnf_stats["g_write_count"] = g_write_count
            vnf_stats["g_write_bytes"] = g_write_bytes

            cur.execute("select packets_recv, bytes_recv, packets_sent, bytes_sent \
                         from guest_vnf_info where vnf = '" + vnf + "' and \
                         timestamp >= '"+start_time+"' and timestamp <= '"+end_time+"'")
            guest_net_counters = cur.fetchall()
            pps_recv, bps_recv, pps_sent, bps_sent = util.get_net_counters(guest_net_counters)

            vnf_stats["pps_recv"] = pps_recv
            vnf_stats["bps_recv"] = bps_recv
            vnf_stats["pps_sent"] = pps_sent
            vnf_stats["bps_sent"] = bps_sent

            cur.execute("select num_threads \
                         from host_vnf_info where vnf = '" + vnf + "' and \
                         timestamp >= '"+start_time+"' and timestamp <= '"+end_time+"'")
            host_num_threads = cur.fetchall()
            h_num_threads = util.get_num_threads(host_num_threads)

            vnf_stats["h_num_threads"] = h_num_threads

            cur.execute("select vol_ctx, invol_ctx \
                         from host_vnf_info where vnf = '" + vnf + "' and \
                         timestamp >= '"+start_time+"' and timestamp <= '"+end_time+"'")
            host_ctx_switches = cur.fetchall()
            h_vol_ctx, h_invol_ctx = util.get_num_ctx_switches(host_ctx_switches)

            vnf_stats["h_vol_ctx"] = h_vol_ctx
            vnf_stats["h_invol_ctx"] = h_invol_ctx

            add_vnf_stats(vnf_stats)

    conn.close()

    return
