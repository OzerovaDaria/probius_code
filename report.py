#!/usr/bin/python

# General libraries
import sys
import sqlite3

# Probius libraries
import util
from common import analysis_database

import smtplib, ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_msg(email, test_case ):

    fromaddr = "ozerova.daria2016@mail.ru"
    toaddr = email  # "s02190164@gse.cs.msu.ru"
    mypass = "jAu30uKV3epUY0g5hNyK"

    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Subject'] = "Fixed problem Probius"

    body = "Problems were fixed in the following testcases:\n\n"

    #if len(sys.argv) != 2:
    if email == "" or test_case == "":
        print("%s [all | testcase]" % (sys.argv[0]))
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

        if test_case != "all" and testcase != test_case:
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

    critical_metrics = False
    critical_metrics_fl = False
    cr_cpu_percent = 10.00
    cr_mem_percent = 3.50
    cr_throughput = 1.12

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
                    critical_metrics = False
                    if float(stats["h_mem_percent"]) >= cr_cpu_percent:
                        critical_metrics = True
                        body += "Percent memory usage exceeded\n\n" 

                    if float(stats["h_cpu_percent"]) >= cr_cpu_percent:
                        critical_metrics = True
                        body += "Percent cpu usage exceeded\n\n"
 
                    if critical_metrics:
                        critical_metrics_fl = True
                        body += "metric values:\n"
                        body += "testcase: " + case + "\n" + "protocol: " + protocol + "\n" + "bandwidth: " + bandwidth + "\n" + "vnf: " + vnf + "\n"
                        # body += "guest_cpu_time: " + stats["g_cpu_time"] + "\n" + "guest_vcpu_time: " + stats["g_vcpu_time"] + "\n" + "guest_user_time: " + stats["g_user_time"] + "\n" + "guest_system_time: " + stats["g_system_time"] + "\n"
                        body += "host_cpu_percent: " + stats["h_cpu_percent"] + "\n" + "host_user_time: " + stats["h_user_time"] + "\n" + "host_system_time: " + stats["h_system_time"] + "\n"
                        body += "host_mem_percent: " + stats["h_mem_percent"] + "\n" + "host_total_mem: " + stats["h_total_mem"] + "\n" + "host_rss_mem: " + stats["h_rss_mem"] + "\n"
                        body += "guest_disk_read_count: " + stats["g_read_count"] + "\n" + "guest_disk_read_bytes: " + stats["g_read_bytes"] + "\n" + "guest_disk_write_count: " + stats[
                                    "g_write_count"] + "\n" + "guest_disk_write_bytes: " + stats["g_write_bytes"] + "\n"
                        body += "recv_pps: " + str(float(stats["pps_recv"])) + "\n" + "recv_Mbps: " + str(
                            float(stats["bps_recv"]) / 1024. / 1024.) + "\n"
                        body += "sent_pps: " + str(float(stats["pps_sent"])) + "\n" + "sent_Mbps: " + str(
                            float(stats["bps_sent"]) / 1024. / 1024.) + "\n"
                        body += "num_threads: " + stats["num_threads"] + "\n" + "voluntary_ctx_switch: " + stats[
                            "vol_ctx"] + "\n" + "involuntary_ctx_switch: " + stats["invol_ctx"] + "\n"

                        body += "\n" + "\n"

    msg.attach(MIMEText(body, 'plain'))
    server = smtplib.SMTP_SSL('smtp.mail.ru', 465)
    # server.starttls()
    server.ehlo()
    server.login(fromaddr, mypass)
    text = msg.as_string()
    if critical_metrics_fl:
        server.sendmail(fromaddr, toaddr, text)
    server.quit()

    return

#send_msg("s02190164@gse.cs.msu.ru", "tcpdump")
