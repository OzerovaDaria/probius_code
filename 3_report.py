#!/usr/bin/python

# General libraries
import sys
import sqlite3

# Probius libraries
import util
from common import analysis_database

if len(sys.argv) != 2:
    print "%s {testcase}" % (sys.argv[0])
    exit(0)

conn = sqlite3.connect(analysis_database)
cur = conn.cursor()

cur.execute("select distinct testcase, protocol, bandwidth, latency from vnf_stats")
testcases = cur.fetchall()

temp_list = []
for idx in range(len(testcases)):
    case = testcases[idx]
    testcase = case[0].replace(")", "(")
    testcase = testcase.split("(")

    for test in testcase:
        if len(test) <= 2:
            testcase.remove(test)

    testcase = ''.join(map(str, testcase))

    if testcase != sys.argv[1]:
        temp_list.append(case)

for temp in temp_list:
    testcases.remove(temp)

results = {}

for idx in range(len(testcases)):
    case = testcases[idx]
    testcase = case[0]
    protocol = case[1]
    bandwidth = case[2]

    results[testcase] = {}

    cur.execute("select vnf from vnf_stats \
                 where testcase = '" + testcase + "' and protocol = '" + protocol + "' and bandwidth = '" + bandwidth + "'")
    vnf_list = cur.fetchall()

    for vnf in vnf_list:
        results[testcase][vnf[0]] = {}

for case in testcases:
    testcase = case[0]
    protocol = case[1]
    bandwidth = case[2]
    latency = case[3]

    cur.execute("select vnf from vnf_stats \
                 where testcase = '" + testcase + "' and protocol = '" + protocol + "' and bandwidth = '" + bandwidth + "'")
    vnf_list = cur.fetchall()

    VNFs = []
    for vnf in vnf_list:
        VNFs.append(vnf[0])

    for vnf in VNFs:
        cur.execute("select * from vnf_stats where testcase = '" + testcase + "' and protocol = '" + protocol + \
                     "' and bandwidth = '" + bandwidth + "' and vnf = '" + vnf + "'")
        vnf_stats = cur.fetchall()

        if protocol not in results[testcase][vnf]:
            results[testcase][vnf][protocol] = {}

        if bandwidth not in results[testcase][vnf][protocol]:
            results[testcase][vnf][protocol][bandwidth] = {}

        results[testcase][vnf][protocol][bandwidth]["g_cpu_time"] = vnf_stats[0][5]
        results[testcase][vnf][protocol][bandwidth]["g_vcpu_time"] = vnf_stats[0][6]
        results[testcase][vnf][protocol][bandwidth]["g_user_time"] = vnf_stats[0][7]
        results[testcase][vnf][protocol][bandwidth]["g_system_time"] = vnf_stats[0][8]

        results[testcase][vnf][protocol][bandwidth]["h_cpu_percent"] = vnf_stats[0][9]
        results[testcase][vnf][protocol][bandwidth]["h_user_time"] = vnf_stats[0][10]
        results[testcase][vnf][protocol][bandwidth]["h_system_time"] = vnf_stats[0][11]

        results[testcase][vnf][protocol][bandwidth]["h_mem_percent"] = vnf_stats[0][12]
        results[testcase][vnf][protocol][bandwidth]["h_total_mem"] = vnf_stats[0][13]
        results[testcase][vnf][protocol][bandwidth]["h_rss_mem"] = vnf_stats[0][14]

        results[testcase][vnf][protocol][bandwidth]["g_read_count"] = vnf_stats[0][15]
        results[testcase][vnf][protocol][bandwidth]["g_read_bytes"] = vnf_stats[0][16]
        results[testcase][vnf][protocol][bandwidth]["g_write_count"] = vnf_stats[0][17]
        results[testcase][vnf][protocol][bandwidth]["g_write_bytes"] = vnf_stats[0][18]

        results[testcase][vnf][protocol][bandwidth]["pps_recv"] = vnf_stats[0][19]
        results[testcase][vnf][protocol][bandwidth]["bps_recv"] = vnf_stats[0][20]
        results[testcase][vnf][protocol][bandwidth]["pps_sent"] = vnf_stats[0][21]
        results[testcase][vnf][protocol][bandwidth]["bps_sent"] = vnf_stats[0][22]

        results[testcase][vnf][protocol][bandwidth]["num_threads"] = vnf_stats[0][23]
        results[testcase][vnf][protocol][bandwidth]["vol_ctx"] = vnf_stats[0][24]
        results[testcase][vnf][protocol][bandwidth]["invol_ctx"] = vnf_stats[0][25]

conn.close()

print "testcase | protocol | bandwidth | vnf | " + \
      "guest_cpu_time | guest_vcpu_time | guest_user_time | guest_system_time | " + \
      "host_cpu_percent | host_user_time | host_system_time | " + \
      "host_mem_percent | host_total_mem | host_rss_mem | " + \
      "guest_disk_read_count | guest_disk_read_bytes | guest_disk_write_count | guest_disk_write_bytes | " + \
      "recv_pps | recv_Mbps | sent_pps | sent_Mbps | " + \
      "num_threads | voluntary_ctx_switch | involuntary_ctx_switch"

for case in results:
    for vnf in results[case]:
        for protocol in results[case][vnf]:
            bwlist = results[case][vnf][protocol].keys()
            keylist = []
            for bw in bwlist:
                keylist.append(int(bw))
            keylist.sort()
            for key in keylist:
                bandwidth = str(key)
                stats = results[case][vnf][protocol][bandwidth]

                print "%s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s" % \
                      (case, protocol, bandwidth, vnf, \
                       stats["g_cpu_time"], stats["g_vcpu_time"], stats["g_user_time"], stats["g_system_time"], \
                       stats["h_cpu_percent"], stats["h_user_time"], stats["h_system_time"], \
                       stats["h_mem_percent"], stats["h_total_mem"], stats["h_rss_mem"], \
                       stats["g_read_count"], stats["g_read_bytes"], stats["g_write_count"], stats["g_write_bytes"], \
                       float(stats["pps_recv"]), float(stats["bps_recv"]) / 1024. / 1024., \
                       float(stats["pps_sent"]), float(stats["bps_sent"]) / 1024. / 1024., \
                       stats["num_threads"], stats["vol_ctx"], stats["invol_ctx"])
