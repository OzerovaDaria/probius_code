#!/usr/bin/python

import sqlite3
import math

import util
from database import ANALYSIS_DATABASE

conn = sqlite3.connect(ANALYSIS_DATABASE)
cur = conn.cursor()

cur.execute("select distinct vnf from vnf_stats")
vnfs = cur.fetchall()

suspicious_cases = {}

for idx in range(len(vnfs)):
    vnf = vnfs[idx][0]

    cur.execute("select * from vnf_stats where vnf = '" + vnf + "'")
    testcases = cur.fetchall()

    labels = []
    extra_labels = []

    x_axis = []

    g_cpu_time = []
    g_vcpu_time = []
    g_user_time = []
    g_system_time = []

    h_cpu_percent = []
    h_user_time = []
    h_system_time = []

    h_mem_percent = []
    h_rss_mem = []

    g_read_count = []
    g_read_bytes = []
    g_write_count = []
    g_write_bytes = []

    pps_recv = []
    bps_recv = []
    pps_sent = []
    bps_sent = []

    h_num_threads = []

    h_vol_ctx = []
    h_invol_ctx = []

    for idx in range(len(testcases)):
        testcase = testcases[idx][0]
        protocol = testcases[idx][1]
        bandwidth = testcases[idx][2]
        latency = testcases[idx][3]
        vnf = testcases[idx][4]

        labels.append(testcase)
        extra_labels.append(vnf)
        x_axis.append(int(bandwidth))

        g_cpu_time.append(float(testcases[idx][5]))
        g_vcpu_time.append(float(testcases[idx][6]))
        g_user_time.append(float(testcases[idx][7]))
        g_system_time.append(float(testcases[idx][8]))

        h_cpu_percent.append(float(testcases[idx][9]))
        h_user_time.append(float(testcases[idx][10]))
        h_system_time.append(float(testcases[idx][11]))

        h_mem_percent.append(float(testcases[idx][12]))
        h_rss_mem.append(float(testcases[idx][14]))

        g_read_count.append(float(testcases[idx][15]))
        g_read_bytes.append(float(testcases[idx][16]))
        g_write_count.append(float(testcases[idx][17]))
        g_write_bytes.append(float(testcases[idx][18]))

        pps_recv.append(float(testcases[idx][19]))
        bps_recv.append(float(testcases[idx][20]))
        pps_sent.append(float(testcases[idx][21]))
        bps_sent.append(float(testcases[idx][22]))

        h_num_threads.append(float(testcases[idx][23]))

        h_vol_ctx.append(float(testcases[idx][24]))
        h_invol_ctx.append(float(testcases[idx][25]))

    D_g_cpu_time = util.cook_distance(x_axis, g_cpu_time)
    D_g_vcpu_time = util.cook_distance(x_axis, g_vcpu_time)
    D_g_user_time = util.cook_distance(x_axis, g_user_time)
    D_g_system_time = util.cook_distance(x_axis, g_system_time)

    D_h_cpu_percent = util.cook_distance(x_axis, h_cpu_percent)
    D_h_user_time = util.cook_distance(x_axis, h_user_time)
    D_h_system_time = util.cook_distance(x_axis, h_system_time)

    D_h_mem_percent = util.cook_distance(x_axis, h_mem_percent)
    D_h_rss_mem = util.cook_distance(x_axis, h_rss_mem)

    D_g_read_count = util.cook_distance(x_axis, g_read_count)
    D_g_read_bytes = util.cook_distance(x_axis, g_read_bytes)
    D_g_write_count = util.cook_distance(x_axis, g_write_count)
    D_g_write_bytes = util.cook_distance(x_axis, g_write_bytes)

    D_pps_recv = util.cook_distance(x_axis, pps_recv)
    D_bps_recv = util.cook_distance(x_axis, bps_recv)
    D_pps_sent = util.cook_distance(x_axis, pps_sent)
    D_bps_sent = util.cook_distance(x_axis, bps_sent)

    D_h_num_threads = util.cook_distance(x_axis, h_num_threads)

    D_h_vol_ctx = util.cook_distance(x_axis, h_vol_ctx)
    D_h_invol_ctx = util.cook_distance(x_axis, h_invol_ctx)

    threshold = 4.0 / len(x_axis)

    for idx in range(len(D_g_cpu_time)):
        if D_g_cpu_time[idx] > threshold:
            if labels[idx] in suspicious_cases:
                if extra_labels[idx] in suspicious_cases[labels[idx]]:
                    suspicious_cases[labels[idx]][extra_labels[idx]] += pow(2, 0)
                else:
                    suspicious_cases[labels[idx]][extra_labels[idx]] = pow(2, 0)
            else:
                suspicious_cases[labels[idx]] = {}
                suspicious_cases[labels[idx]][extra_labels[idx]] = pow(2, 0)

    for idx in range(len(D_g_vcpu_time)):
        if D_g_vcpu_time[idx] > threshold:
            if labels[idx] in suspicious_cases:
                if extra_labels[idx] in suspicious_cases[labels[idx]]:
                    suspicious_cases[labels[idx]][extra_labels[idx]] += pow(2, 1)
                else:
                    suspicious_cases[labels[idx]][extra_labels[idx]] = pow(2, 1)
            else:
                suspicious_cases[labels[idx]] = {}
                suspicious_cases[labels[idx]][extra_labels[idx]] = pow(2, 1)

    for idx in range(len(D_g_user_time)):
        if D_g_user_time[idx] > threshold:
            if labels[idx] in suspicious_cases:
                if extra_labels[idx] in suspicious_cases[labels[idx]]:
                    suspicious_cases[labels[idx]][extra_labels[idx]] += pow(2, 2)
                else:
                    suspicious_cases[labels[idx]][extra_labels[idx]] = pow(2, 2)
            else:
                suspicious_cases[labels[idx]] = {}
                suspicious_cases[labels[idx]][extra_labels[idx]] = pow(2, 2)

    for idx in range(len(D_g_system_time)):
        if D_g_system_time[idx] > threshold:
            if labels[idx] in suspicious_cases:
                if extra_labels[idx] in suspicious_cases[labels[idx]]:
                    suspicious_cases[labels[idx]][extra_labels[idx]] += pow(2, 3)
                else:
                    suspicious_cases[labels[idx]][extra_labels[idx]] = pow(2, 3)
            else:
                suspicious_cases[labels[idx]] = {}
                suspicious_cases[labels[idx]][extra_labels[idx]] = pow(2, 3)

    for idx in range(len(D_h_cpu_percent)):
        if D_h_cpu_percent[idx] > threshold:
            if labels[idx] in suspicious_cases:
                if extra_labels[idx] in suspicious_cases[labels[idx]]:
                    suspicious_cases[labels[idx]][extra_labels[idx]] += pow(2, 4)
                else:
                    suspicious_cases[labels[idx]][extra_labels[idx]] = pow(2, 4)
            else:
                suspicious_cases[labels[idx]] = {}
                suspicious_cases[labels[idx]][extra_labels[idx]] = pow(2, 4)

    for idx in range(len(D_h_user_time)):
        if D_h_user_time[idx] > threshold:
            if labels[idx] in suspicious_cases:
                if extra_labels[idx] in suspicious_cases[labels[idx]]:
                    suspicious_cases[labels[idx]][extra_labels[idx]] += pow(2, 5)
                else:
                    suspicious_cases[labels[idx]][extra_labels[idx]] = pow(2, 5)
            else:
                suspicious_cases[labels[idx]] = {}
                suspicious_cases[labels[idx]][extra_labels[idx]] = pow(2, 5)

    for idx in range(len(D_h_system_time)):
        if D_h_system_time[idx] > threshold:
            if labels[idx] in suspicious_cases:
                if extra_labels[idx] in suspicious_cases[labels[idx]]:
                    suspicious_cases[labels[idx]][extra_labels[idx]] += pow(2, 6)
                else:
                    suspicious_cases[labels[idx]][extra_labels[idx]] = pow(2, 6)
            else:
                suspicious_cases[labels[idx]] = {}
                suspicious_cases[labels[idx]][extra_labels[idx]] = pow(2, 6)

    for idx in range(len(D_h_mem_percent)):
        if D_h_mem_percent[idx] > threshold:
            if labels[idx] in suspicious_cases:
                if extra_labels[idx] in suspicious_cases[labels[idx]]:
                    suspicious_cases[labels[idx]][extra_labels[idx]] += pow(2, 7)
                else:
                    suspicious_cases[labels[idx]][extra_labels[idx]] = pow(2, 7)
            else:
                suspicious_cases[labels[idx]] = {}
                suspicious_cases[labels[idx]][extra_labels[idx]] = pow(2, 7)

    for idx in range(len(D_g_read_count)):
        if D_g_read_count[idx] > threshold:
            if labels[idx] in suspicious_cases:
                if extra_labels[idx] in suspicious_cases[labels[idx]]:
                    suspicious_cases[labels[idx]][extra_labels[idx]] += pow(2, 8)
                else:
                    suspicious_cases[labels[idx]][extra_labels[idx]] = pow(2, 8)
            else:
                suspicious_cases[labels[idx]] = {}
                suspicious_cases[labels[idx]][extra_labels[idx]] = pow(2, 8)

    for idx in range(len(D_g_write_count)):
        if D_g_write_count[idx] > threshold:
            if labels[idx] in suspicious_cases:
                if extra_labels[idx] in suspicious_cases[labels[idx]]:
                    suspicious_cases[labels[idx]][extra_labels[idx]] += pow(2, 9)
                else:
                    suspicious_cases[labels[idx]][extra_labels[idx]] = pow(2, 9)
            else:
                suspicious_cases[labels[idx]] = {}
                suspicious_cases[labels[idx]][extra_labels[idx]] = pow(2, 9)

    for idx in range(len(D_bps_recv)):
        if D_bps_recv[idx] > threshold:
            if labels[idx] in suspicious_cases:
                if extra_labels[idx] in suspicious_cases[labels[idx]]:
                    suspicious_cases[labels[idx]][extra_labels[idx]] += pow(2, 10)
                else:
                    suspicious_cases[labels[idx]][extra_labels[idx]] = pow(2, 10)
            else:
                suspicious_cases[labels[idx]] = {}
                suspicious_cases[labels[idx]][extra_labels[idx]] = pow(2, 10)

for case in sorted(suspicious_cases, key=suspicious_cases.get, reverse=True):
    print case
    for vnf in sorted(suspicious_cases[case], key=suspicious_cases[case].get, reverse=True):
        print "  ", vnf, "->",
        if suspicious_cases[case][vnf] & pow(2, 0):
            print "g_cpu_time ",
        elif suspicious_cases[case][vnf] & pow(2, 1):
            print "g_vcpu_time ",
        elif suspicious_cases[case][vnf] & pow(2, 2):
            print "g_user_time ",
        elif suspicious_cases[case][vnf] & pow(2, 3):
            print "g_system_time ",
        elif suspicious_cases[case][vnf] & pow(2, 4):
            print "h_cpu_percent ",
        elif suspicious_cases[case][vnf] & pow(2, 5):
            print "h_user_time ",
        elif suspicious_cases[case][vnf] & pow(2, 6):
            print "h_system_time ",
        elif suspicious_cases[case][vnf] & pow(2, 7):
            print "h_mem_percent ",
        elif suspicious_cases[case][vnf] & pow(2, 8):
            print "g_read_count ",
        elif suspicious_cases[case][vnf] & pow(2, 9):
            print "g_write_count ",
        elif suspicious_cases[case][vnf] & pow(2, 10):
            print "bps_recv ",
        else:
            print suspicious_cases[case][vnf],
    print

conn.close()
