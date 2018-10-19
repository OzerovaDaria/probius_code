# General libraries
import math
import subprocess
import numpy as np
import statsmodels.api as sm

# Probius libraries
# Nothing to import

# Statistics #

def get_difference(values):
    return [x - values[i - 1] for i, x in enumerate(values)][1:]

def get_maximum(values):
    mx = values[0]

    for value in values:
        if value > mx:
            mx = value

    return mx

def get_minimum(values):
    mn = values[0]

    for value in values:
        if value < mn:
            mn = value

    return mn

def get_M(values):
    tmp = []

    for value in values:
        tmp.append(value)

    tmp.sort()
    length = len(tmp)
    median = length / 2

    if length % 2 == 1:
        return tmp[median]
    else:
        return ((tmp[median - 1] + tmp[median]) * 1.0) / 2

def get_S(values):
    tmp = []

    for value in values:
        tmp.append(value)

    tmp.sort()
    length = len(tmp)
    avg = (sum(tmp) * 1.0) / length

    dev = []
    for x in tmp:
        dev.append(x - avg)

    sqr = []
    for x in dev:
        sqr.append(x * x)

    if len(sqr) <= 1:
        return 0.0

    mean = sum(sqr) / len(sqr)

    return math.sqrt(sum(sqr) / (len(sqr) - 1))

def get_average(values, flag=False):
    if len(values) == 0:
        return 0.0

    tmp = []

    for value in values:
        tmp.append(value)

    tmp.sort()

    if flag == True:
        med_tmp = get_M(tmp)
        std_tmp = get_S(tmp)

        if len(tmp) >= 3:
            for t in tmp:
                if t < (med_tmp - (std_tmp * 0.34)):
                    tmp.remove(t)
                elif t > (med_tmp + (std_tmp * 0.34)):
                    tmp.remove(t)

    return (sum(tmp) * 1.0) / len(tmp)

def get_median(values, flag=False):
    if len(values) == 0:
        return 0.0

    tmp = []

    for value in values:
        tmp.append(value)

    tmp.sort()

    if flag == True:
        med_tmp = get_M(tmp)
        std_tmp = get_S(tmp)

        if len(tmp) >= 3:
            for t in tmp:
                if t < (med_tmp - (std_tmp * 0.34)):
                    tmp.remove(t)
                elif t > (med_tmp + (std_tmp * 0.34)):
                    tmp.remove(t)

    length = len(tmp)
    median = length / 2

    if length % 2 == 1:
        return tmp[median]
    else:
        return ((tmp[median - 1] + tmp[median]) * 1.0) / 2

def get_stdev(values, flag=False):
    if len(values) == 0:
        return 0.0

    tmp = []

    for value in values:
        tmp.append(value)

    tmp.sort()

    if flag == True:
        med_tmp = get_M(tmp)
        std_tmp = get_S(tmp)

        if len(tmp) >= 3:
            for t in tmp:
                if t < (med_tmp - (std_tmp * 0.34)):
                    tmp.remove(t)
                elif t > (med_tmp + (std_tmp * 0.34)):
                    tmp.remove(t)

    length = len(tmp)
    avg = (sum(tmp) * 1.0) / length

    dev = []
    for x in tmp:
        dev.append(x - avg)

    sqr = []
    for x in dev:
        sqr.append(x * x)

    if len(sqr) <= 1:
        return 0.0

    mean = sum(sqr) / len(sqr)

    return math.sqrt(sum(sqr) / (len(sqr) - 1))

# Summary #

def get_latency(latencies):
    values = []
    for latency in latencies:
        values.append(float(latency[0]))

    return get_median(values, True)

def get_guest_cpu_time(guest_cpu_times):
    cpu = []
    vcpu = []
    user = []
    system = []
    for guest_cpu_time in guest_cpu_times:
        cpu.append(float(guest_cpu_time[0]))
        vcpu.append(float(guest_cpu_time[1]))
        user.append(float(guest_cpu_time[2]))
        system.append(float(guest_cpu_time[3]))

    return get_median(cpu, True), \
           get_median(vcpu, True), \
           get_median(user, True), \
           get_median(system, True)

def get_host_cpu_time(host_cpu_times):
    cpu = []
    user = []
    system = []
    for host_cpu_time in host_cpu_times:
        cpu.append(float(host_cpu_time[0]))
        user.append(float(host_cpu_time[1]))
        system.append(float(host_cpu_time[2]))

    return get_median(cpu, True), \
           get_median(user, True), \
           get_median(system, True)

def get_mem_usage(mem_usages):
    mem_percent = []
    total_mem = []
    rss_mem = []
    for mem_usage in mem_usages:
        mem_percent.append(float(mem_usage[0]))
        total_mem.append(float(mem_usage[1]))
        rss_mem.append(float(mem_usage[2]))

    return get_median(mem_percent, True), \
           get_median(total_mem, True), \
           get_median(rss_mem, True)

def get_io_counters(io_counters):
    read_count = []
    read_bytes = []
    write_count = []
    write_bytes = []
    for io_counter in io_counters:
        read_count.append(float(io_counter[0]))
        read_bytes.append(float(io_counter[1]))
        write_count.append(float(io_counter[2]))
        write_bytes.append(float(io_counter[3]))

    return get_median(read_count, True), \
           get_median(read_bytes, True), \
           get_median(write_count, True), \
           get_median(write_bytes, True)

def get_net_counters(net_counters):
    pps_recv = []
    bps_recv = []
    pps_sent = []
    bps_sent = []
    for net_counter in net_counters:
        pps_recv.append(float(net_counter[0]))
        bps_recv.append(float(net_counter[1]) * 8.0)
        pps_sent.append(float(net_counter[2]))
        bps_sent.append(float(net_counter[3]) * 8.0)

    return get_median(pps_recv, True), \
           get_median(bps_recv, True), \
           get_median(pps_sent, True), \
           get_median(bps_sent, True)

def get_num_threads(num_threads):
    threads = []
    for num_thread in num_threads:
        threads.append(float(num_thread[0]))

    return get_median(threads, True)

def get_num_ctx_switches(num_ctx_switches):
    vol_ctx = []
    invol_ctx = []
    for num_ctx_switch in num_ctx_switches:
        vol_ctx.append(float(num_ctx_switch[0]))
        invol_ctx.append(float(num_ctx_switch[1]))

    return get_median(vol_ctx, True), \
           get_median(invol_ctx, True)

# Anomaly detection #

def cook_distance(X_list, y_list):
    model = sm.OLS

    X = np.array(X_list)
    X = sm.add_constant(X)

    y = np.array(y_list)

    n = len(X)

    fitted = model(y, X).fit()
    yhat = fitted.predict(X)

    p = len(fitted.params)
    mse = np.sum((yhat - y)**2.0) / n
    denom = p * mse

    idx = np.arange(n)

    D = np.array([np.sum((yhat - model(y[idx!=i], X[idx!=i]).fit().predict(X))**2.0) for i in range(n)]) / denom

    return D.tolist()
