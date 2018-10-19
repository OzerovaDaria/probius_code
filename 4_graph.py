#!/usr/bin/python

# General libraries
import sys
import sqlite3
from graph_tool.all import *

# Probius libraries
from common import analysis_database

yellow = '#eae88a'
pink = '#ea8ad9'
purple = '#a98aea'
blue = '#8a93ea'
sky = '#8ad2ea'
green = '#8aeabd'
grass = '#96ea8a'
red = '#ea8a8a'
orange = '#eab08a'
brown = '#967e7e'

def find_vertex(vertex, label, v_len):
    i = 0

    while i<v_len:
        if label[i] == vertex:
            return i
        i += 1

    return -1

def generate_graphs(testcase):
    conn = sqlite3.connect(analysis_database)
    cur = conn.cursor()

    cur.execute("select * from testcase where testcase = '" + testcase + "' order by start_time")
    _testcase = cur.fetchall()

    graphv = {}
    graphs = {}
    labels = {}
    e_colors = {}
    e_times = {}

    print "testcase | protocol | bandwidth | vnf | cpu_nums | " + \
          "Computation | Initialization | Hard switch | Soft switch | " + \
          "Memory access | I/O operation | Interrupt | Idleness | " + \
          "Lock contention | IRQ | Others | Outside | " + \
          "MSR_WRITE | EXTERNAL_INTERRUPT | PAUSE_INSTRUCTION | " + \
          "EPT_VIOLATION | IO_INSTRUCTION | EXCEPTION_NMI | " + \
          "EPT_MISCONFIG | HLT"
     
    for _case in _testcase:
        case= _case[0]
        protocol = _case[1]
        bandwidth = _case[2]
        start_time = _case[3]
        end_time = _case[4]
        cpu_nums= {}

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
        
        cur.execute("select pid from trace_info_pid where timestamp >= '" + start_time+ \
                    "' and timestamp <= '" + end_time+ "' group by pid order by timestamp")
        _pid = cur.fetchall()

        k = 0 
        for vnf in case.split(","):
            _stats = {}
            _stats = {}
            
            _stats["testcase"] = VNFs
            _stats["protocol"] = protocol
            _stats["bandwidth"] = bandwidth
            _stats["vnf"] = vnf

            cur.execute("select distinct pre_event, pre_data from trace_info_pid where pid = '" + _pid[k][0] + "'")
            names = cur.fetchall()

            cur.execute("select * from trace_info_pid where pid = '" + _pid[k][0] + "'")
            trace = cur.fetchall()

            dist_name = []
            for j in range(len(names)):
                if names[j][0] == 'vcpu_match_mmio':
                    continue
                elif names[j][0] == 'kvm_apic_ipi':
                    continue
                elif names[j][0].find('irq') > 0:
                    continue
                elif names[j][0] != 'kvm_fpu' and names[j][0] != 'kvm_exit' and names[j][0] != 'kvm_vcpu_wakeup':
                    dist_name.append(names[j][0][4:])
                else:
                    dist_name.append(names[j][0][4:] + '(' + names[j][1] + ')')
            dist_name = list(set(dist_name))
            
            g = Graph(directed=True)
            label = g.new_vertex_property("string")

            i = 0
            vlist = []
            for name in dist_name:
                v = g.add_vertex()
                label[v] = name
                i+=1
                vlist.append(v)
                
            e_color = g.new_edge_property("string")
            e_count = g.new_edge_property("int")
            e_time = g.new_edge_property("float")

            default_color = '#2e3436'

            elist = []
            for _trace in trace:
                pre_event = _trace[2]
                curr_event = _trace[6]

                if pre_event != 'kvm_fpu' and _trace[2] != 'kvm_exit' and _trace[2] != 'kvm_vcpu_wakeup':
                    src = find_vertex(pre_event[4:], label, i)
                else:
                    src = find_vertex(pre_event[4:] + '(' + _trace[5] + ')', label, i)

                if curr_event != 'kvm_fpu' and _trace[6] != 'kvm_exit' and _trace[6] != 'kvm_vcpu_wakeup':
                    dst = find_vertex(curr_event[4:], label, i)
                else:
                    dst = find_vertex(curr_event[4:] + '(' + _trace[9] + ')', label, i)

                if src == -1 or dst == -1:
                    continue

                if g.edge(src,dst) is not None:
                    e_count[src,dst] = (e_count[src,dst] + int(_trace[10]))
                    e_time[src,dst] = (e_time[src,dst] + float(_trace[11]))            
                else:
                    e = g.add_edge(src, dst)     
                    e_count[e] = int(_trace[10])
                    e_time[e] = float(_trace[11])
                    elist.append(e)
                    e_color[e] = default_color

            # initialization
            init_time = 0
            init_count = 0

            # computation
            computation_time = 0
            computation_count = 0

            # hard context-switch
            hw_time = 0
            hw_count = 0

            # soft context-switch
            sw_time = 0
            sw_count = 0

            # memory access
            mem_time = 0
            mem_count = 0

            # IO operation
            io_time = 0
            io_count = 0

            # interrupt
            inte_time = 0
            inte_count = 0

            # idleness
            idle_time = 0
            idle_count = 0

            # lock connection
            lock_time = 0
            lock_count = 0

            # outsides (other processes are running)
            out_time = 0
            out_count = 0

            # unknown (undefined ones)
            unknown_time = 0
            unknown_count = 0

            # sub events
            irq_time = 0
            irq_count = 0
            msr_time = 0
            msr_count = 0
            exter_time = 0
            exter_count = 0
            pause_time = 0
            pause_count = 0
            vio_time = 0
            vio_count = 0
            hlt_time = 0
            hlt_count = 0
            ioins_time = 0
            ioins_count = 0
            mis_time = 0
            mis_count = 0
            nmi_time = 0
            nmi_count = 0

            for e in elist:
                if label[e.source()] == 'entry':
                    computation_time += e_time[e]
                    computation_count += e_count[e]
                    e_color[e] = brown

                elif label[e.source()] == 'ple_window' and label[e.target()] == 'vcpu_wakeup(wait)':
                    init_time += e_time[e]
                    init_count += e_count[e]
                    e_color[e] = orange 

                elif label[e.source()] == 'ple_window' and label[e.target()] == 'entry':
                    init_time += e_time[e]
                    init_count += e_count[e] 
                    e_color[e] = orange

                elif label[e.source()] == 'ple_window' and label[e.target()] == 'fpu(load)':
                    init_time += e_time[e]
                    init_count += e_count[e]
                    e_color[e] = orange

                elif label[e.source()] == 'ple_window' and label[e.target()] == 'fpu(unload)':
                    hw_time += e_time[e]
                    hw_count += e_count[e]
                    e_color[e] = red

                elif label[e.source()] == 'ple_window' and label[e.target()] == 'ple_window':
                    unknown_time += e_time[e]
                    unknown_count += e_count[e]

                elif label[e.source()] == 'vcpu_wakeup(wait)' and label[e.target()] == 'fpu(load)':
                    init_time += e_time[e]
                    init_count += e_count[e]
                    e_color[e] = orange

                elif label[e.source()] == 'vcpu_wakeup(wait)' and label[e.target()] == 'ple_window':
                    init_time += e_time[e]
                    init_count += e_count[e]
                    e_color[e] = orange

                elif label[e.source()] == 'vcpu_wakeup(wait)' and label[e.target()] == 'entry':
                    init_time += e_time[e]
                    init_count += e_count[e]
                    e_color[e] = orange

                elif label[e.source()] == 'fpu(load)' and label[e.target()] == 'entry':
                    init_time += e_time[e]
                    init_count += e_count[e]
                    e_color[e] = orange

                elif label[e.source()] == 'exit(MSR_WRITE)' and label[e.target()] == 'msr':
                    mem_time += e_time[e]
                    msr_time += e_time[e]
                    mem_count += e_count[e]
                    msr_count += e_count[e]
                    e_color[e] = yellow

                elif label[e.source()] == 'exit(MSR_WRITE)' and label[e.target()] == 'apic':
                    mem_time += e_time[e]
                    msr_time += e_time[e]
                    mem_count += e_count[e]
                    msr_count += e_count[e]
                    e_color[e] = yellow

                elif label[e.source()] == 'apic' and label[e.target()] == 'msr':
                    mem_time += e_time[e]
                    msr_time += e_time[e]
                    mem_count += e_count[e]
                    msr_count += e_count[e]
                    e_color[e] = yellow

                elif label[e.source()] == 'apic' and label[e.target()] == 'apic':
                    mem_time += e_time[e]
                    msr_time += e_time[e]
                    mem_count += e_count[e]
                    msr_count += e_count[e]
                    e_color[e] = yellow

                elif label[e.source()] == 'msr' and label[e.target()] == 'entry':
                    mem_time += e_time[e]
                    msr_time += e_time[e]
                    mem_count += e_count[e]
                    msr_count += e_count[e]
                    e_color[e] = yellow

                elif label[e.source()] == 'msr' and label[e.target()] == 'fpu(unload)':
                    hw_time += e_time[e]
                    msr_time += e_time[e]
                    hw_count += e_count[e]
                    msr_count += e_count[e]
                    e_color[e] = red

                elif label[e.source()] == 'exit(HLT)' and label[e.target()] == 'fpu(unload)':
                    idle_time += e_time[e]
                    hlt_time += e_time[e]
                    idle_count += e_count[e]
                    hlt_count += e_count[e]
                    e_color[e] = purple

                elif label[e.source()] == 'exit(HLT)' and label[e.target()] == 'vcpu_wakeup(poll)':
                    idle_time += e_time[e]
                    hlt_time += e_time[e]
                    idle_count += e_count[e]
                    hlt_count += e_count[e]
                    e_color[e] = purple

                elif label[e.source()] == 'exit(HLT)' and label[e.target()] == 'vcpu_wakeup(wait)':
                    idle_time += e_time[e]
                    hlt_time += e_time[e]
                    idle_count += e_count[e]
                    hlt_count += e_count[e]
                    e_color[e] = purple

                elif label[e.source()] == 'exit(HLT)' and label[e.target()] == 'entry':
                    idle_time += e_time[e]
                    hlt_time += e_time[e]
                    idle_count += e_count[e]
                    hlt_count += e_count[e]
                    e_color[e] = purple

                elif label[e.source()] == 'exit(HLT)' and label[e.target()] == 'halt_poll_ns':
                    idle_time += e_time[e]
                    hlt_time += e_time[e]
                    idle_count += e_count[e]
                    hlt_count += e_count[e]
                    e_color[e] = purple

                elif label[e.source()] == 'halt_poll_ns' and label[e.target()] == 'vcpu_wakeup(poll)':
                    idle_time += e_time[e]
                    hlt_time += e_time[e]
                    idle_count += e_count[e]
                    hlt_count += e_count[e]
                    e_color[e] = purple 

                elif label[e.source()] == 'halt_poll_ns' and label[e.target()] == 'vcpu_wakeup(wait)':
                    idle_time += e_time[e]
                    hlt_time += e_time[e]
                    idle_count += e_count[e]
                    hlt_count += e_count[e]
                    e_color[e] = purple

                elif label[e.source()] == 'fpu(unload)' and label[e.target()] == 'ple_window':
                    out_time += e_time[e]
                    out_count += e_count[e]

                elif label[e.source()] == 'fpu(unload)' and label[e.target()] == 'fpu(load)':
                    hw_time += e_time[e]
                    hw_count += e_count[e]
                    e_color[e] = red

                elif label[e.source()] == 'fpu(load)' and label[e.target()] == 'fpu(unload)':
                    hw_time += e_time[e]
                    hw_count += e_count[e] 
                    e_color[e] = red

                elif label[e.source()] == 'fpu(unload)' and label[e.target()] == 'mmio':
                    mem_time += e_time[e]
                    mem_count += e_count[e]
                    e_color[e] = yellow

                elif label[e.source()] == 'fpu(unload)' and label[e.target()] == 'pio':
                    io_time += e_time[e]
                    io_count += e_count[e]
                    ioins_time += e_time[e]
                    ioins_count += e_count[e]
                    e_color[e] = grass

                elif label[e.source()] == 'exit(EPT_MISCONFIG)' and label[e.target()] == 'emulate_insn':
                    mem_time += e_time[e]
                    mis_time += e_time[e]
                    mem_count += e_count[e]
                    mis_count += e_count[e]
                    e_color[e] = yellow

                elif label[e.source()] == 'emulate_insn' and label[e.target()] == 'vcpu_match_mmio':
                    mem_time += e_time[e]
                    mis_time += e_time[e]
                    mem_count += e_count[e]
                    mis_count += e_count[e]
                    e_color[e] = yellow

                elif label[e.source()] == 'vcpu_match_mmio' and label[e.target()] == 'mmio':
                    mem_time += e_time[e]
                    mis_time += e_time[e]
                    mem_count += e_count[e]
                    mis_count += e_count[e]
                    e_color[e] = yellow

                elif label[e.source()] == 'mmio' and label[e.target()] == 'userspace_exit':
                    mem_time += e_time[e]
                    mis_time += e_time[e]
                    mem_count += e_count[e]
                    mis_count += e_count[e]
                    e_color[e] = yellow

                elif label[e.source()] == 'mmio' and label[e.target()] == 'fpu(load)':
                    mem_time += e_time[e]
                    mem_time += e_time[e]
                    e_color[e] = yellow

                elif label[e.source()] == 'mmio' and label[e.target()] == 'fpu(unload)':
                    hw_time += e_time[e]
                    hw_time += e_time[e]
                    e_color[e] = red

                elif label[e.source()] == 'mmio' and label[e.target()] == 'entry':
                    mem_count += e_count[e]
                    mem_count += e_count[e]
                    e_color[e] = yellow

                elif label[e.source()] == 'exit(EXTERNAL_INTERRUPT)' and label[e.target()] == 'entry':
                    inte_time += e_time[e]
                    exter_time += e_time[e]
                    inte_count += e_count[e]
                    exter_count += e_count[e]
                    e_color[e] = green

                elif label[e.source()] == 'exit(EXTERNAL_INTERRUPT)' and label[e.target()] == 'fpu(unload)':
                    hw_time += e_time[e]
                    exter_time += e_time[e]
                    hw_count += e_count[e]
                    exter_count += e_count[e]
                    e_color[e] = red

                elif label[e.source()] == 'exit(IO_INSTRUCTION)' and label[e.target()] == 'pio':
                    io_time += e_time[e]
                    ioins_time += e_time[e]
                    io_count += e_count[e]
                    ioins_count += e_count[e]
                    e_color[e] = grass

                elif label[e.source()] == 'exit(IO_INSTRUCTION)' and label[e.target()] == 'emulate_insn':
                    io_time += e_time[e]
                    ioins_time += e_time[e]
                    io_count += e_count[e]
                    ioins_count += e_count[e]
                    e_color[e] = grass

                elif label[e.source()] == 'emulate_insn' and label[e.target()] == 'userspace_exit':
                    io_time += e_time[e]
                    ioins_time += e_time[e]
                    io_count += e_count[e]
                    ioins_count += e_count[e]
                    e_color[e] = grass

                elif label[e.source()] == 'emulate_insn' and label[e.target()] == 'entry':
                    io_time += e_time[e]
                    ioins_time += e_time[e]
                    io_count += e_count[e]
                    ioins_count += e_count[e]
                    e_color[e] = grass

                elif label[e.source()] == 'emulate_insn' and label[e.target()] == 'pio':
                    io_time += e_time[e]
                    ioins_time += e_time[e]
                    io_count += e_count[e]
                    ioins_count += e_count[e]
                    e_color[e] = grass

                elif label[e.source()] == 'pio' and label[e.target()] == 'entry':
                    io_time += e_time[e]
                    ioins_time += e_time[e]
                    io_count += e_count[e]
                    ioins_count += e_count[e]
                    e_color[e] = grass

                elif label[e.source()] == 'pio' and label[e.target()] == 'fpu(unload)':
                    hw_time += e_time[e]
                    hw_count += e_count[e]
                    e_color[e] = red

                elif label[e.source()] == 'pio' and label[e.target()] == 'fpu(load)':
                    io_time += e_time[e]
                    ioins_time += e_time[e]
                    io_count += e_count[e]
                    ioins_count += e_count[e]
                    e_color[e] = grass

                elif label[e.source()] == 'pio' and label[e.target()] == 'userspace_exit':
                    io_time += e_time[e]
                    ioins_time += e_time[e]
                    io_count += e_count[e]
                    ioins_count += e_count[e]
                    e_color[e] = grass

                elif label[e.source()] == 'userspace_exit' and label[e.target()] == 'fpu(unload)':
                    hw_time += e_time[e]
                    hw_count += e_count[e]
                    e_color[e] = red

                elif label[e.source()] == 'vcpu_wakeup(poll)' and label[e.target()] == 'entry':
                    sw_time += e_time[e]
                    sw_count += e_count[e]
                    e_color[e] = blue

                elif label[e.source()] == 'ple_window' and label[e.target()] == 'halt_poll_ns':
                    sw_time += e_time[e]
                    sw_count += e_count[e]
                    e_color[e] = blue

                elif label[e.source()] == 'ple_window' and label[e.target()] == 'vcpu_wakeup(poll)':
                    sw_time += e_time[e]
                    sw_count += e_count[e]
                    e_color[e] = blue
            
                elif label[e.source()] == 'vcpu_wakeup(poll)' and label[e.target()] == 'ple_window':
                    sw_time += e_time[e]
                    sw_count += e_count[e]
                    e_color[e] = blue

                elif label[e.source()] == 'vcpu_wakeup(poll)' and label[e.target()] == 'fpu(unload)':
                    hw_time += e_time[e]
                    hw_count += e_count[e]
                    e_color[e] = red

                elif label[e.source()] == 'vcpu_wakeup(poll)' and label[e.target()] == 'fpu(load)':
                    hw_time += e_time[e]
                    hw_count += e_count[e]
                    e_color[e] = red

                elif label[e.source()] == 'exit(PAUSE_INSTRUCTION)' and label[e.target()] == 'ple_window':
                    lock_time += e_time[e]
                    lock_count += e_count[e]    
                    pause_time += e_time[e]
                    pause_count += e_count[e]

                elif label[e.source()] == 'exit(CPUID)' and label[e.target()] == 'cpuid':
                    unknown_time += e_time[e]
                    unknown_count += e_count[e]

                elif label[e.source()] == 'cpuid' and label[e.target()] == 'entry':
                    unknown_time += e_time[e]
                    unknown_count += e_count[e]
                    
                elif label[e.source()] == 'fpu(unload)' and label[e.target()] == 'set_irq':
                    irq_time += e_time[e]
                    irq_count += e_count[e]

                elif label[e.source()] == 'set_irq' and label[e.target()] == 'pic_set_irq':
                    irq_time += e_time[e]
                    irq_count += e_count[e]

                elif label[e.source()] == 'pic_set_irq' and label[e.target()] == 'pio':
                    irq_time += e_time[e]
                    irq_count += e_count[e]

                elif label[e.source()] == 'pic_set_irq' and label[e.target()] == 'fpu(load)':
                    irq_time += e_time[e]
                    irq_count += e_count[e]

                elif label[e.source()] == 'pic_set_irq' and label[e.target()] == 'ple_window':
                    irq_time += e_time[e]
                    irq_count += e_count[e]

                elif label[e.source()] == 'fpu(unload)' and label[e.target()] == 'msi_set_irq':
                    irq_time += e_time[e]
                    irq_count += e_count[e]

                elif label[e.source()] == 'msi_set_irq' and label[e.target()] == 'ple_window':
                    irq_time += e_time[e]
                    irq_count += e_count[e]

                elif label[e.source()] == 'msi_set_irq' and label[e.target()] == 'msi_set_irq':
                    irq_time += e_time[e]
                    irq_count += e_count[e]

                elif label[e.source()] == 'ple_window' and label[e.target()] == 'msi_set_irq':
                    irq_time += e_time[e]
                    irq_count += e_count[e]

                elif label[e.source()] == 'exit(EXCEPTION_NMI)' and label[e.target()] == 'entry':
                    nmi_time += e_time[e]
                    inte_time += e_time[e]
                    nmi_count += e_count[e]
                    inte_count += e_count[e]
                    e_color[e] = green

                elif label[e.source()] == 'exit(EPT_VIOLATION)' and label[e.target()] == 'page_fault':
                    vio_time += e_time[e]
                    mem_time += e_time[e]
                    vio_count += e_count[e]
                    mem_count += e_count[e]
                    e_color[e] = yellow

                elif label[e.source()] == 'page_fault' and label[e.target()] == 'entry':
                    vio_time += e_time[e]
                    mem_time += e_time[e]
                    vio_count += e_count[e]
                    mem_count += e_count[e]
                    e_color[e] = yellow

                else:
                    unknown_time += e_time[e]
                    unknown_count += e_count[e]

            print "%s | %s | %s | %s | %s | %f | %d | %f | %d | %f | %d | %f | %d | %f | %d | " + \
                  "%f | %d | %f | %d | %f | %d | %f | %d | %f | %d | %f | %d | %f | %d | %f | %d | " + \
                  "%f | %d | %f | %d | %f | %d | %f | %d | %f | %d | %f | %d | %f | %d" % \
                  (case, protocol, bandwidth, vnf, str(cpu_nums[vnf]), \
                   computation_time, computation_count, init_time, init_count, \
                   hw_time, hw_count, sw_time, sw_count, mem_time, mem_count, \
                   io_time, io_count, inte_time, inte_count, idle_time, idle_count, \
                   lock_time, lock_count, irq_time, irq_count, \
                   unknown_time, unknown_count, out_time, out_count, \
                   msr_time, msr_count, exter_time, exter_count, pause_time, pause_count, \
                   vio_time, vio_count, ioins_time, ioins_count, nmi_time, nmi_count, \
                   mis_time, mis_count, hlt_time, hlt_count)

            k += 1

            for v in vlist:
                if label[v] == 'fpu(load)':
                    label[v] = 'vmcs(load)'
                if label[v] == 'fpu(unload)':
                    label[v] = 'vmcs(unload)'
                if label[v] == 'ple_window':
                    label[v] = 'pause_loop_exit'
                if label[v] == 'exit(PAUSE_INSTRUCTION)':
                    label[v] = 'exit(pause_instruction)'
                if label[v] == 'exit(IO_INSTRUCTION)':
                    label[v] = 'exit(io_insturction)'
                if label[v] == 'exit(CPUID)':
                    label[v] = 'exit(cpuid)'
                if label[v] == 'exit(HLT)':
                    label[v] = 'exit(hlt)'
                if label[v] == 'exit(EPT_MISCONFIG)':
                    label[v] = 'exit(ept_misconfig)'
                if label[v] == 'exit(EXCEPTION_NMI)':
                    label[v] = 'exit(exception_nmi)'
                if label[v] == 'exit(EPT_VIOLATION)':
                    label[v] = 'exit(ept_violation)'
                if label[v] == 'exit(MSR_WRITE)':
                    label[v] = 'exit(msr_write)'
                if label[v] == 'exit(EXTERNAL_INTERRUPT)':
                    label[v] = 'exit(external_interrupt)'
            
            for e in elist:
                if e_time[e] <= 0.001:
                    e_time[e] = 0.5
                elif e_time[e] <= 0.01:
                    e_time[e] = 1
                elif e_time[e] <= 0.1:
                    e_time[e] = 1.5
                elif e_time[e] <= 1:
                    e_time[e] = 2
                else:
                    e_time[e] = 2.5

            key = protocol + '_' + bandwidth + '_' + vnf

            graphv[key] = [g, label, e_color, e_time]
            graphs[key] = g
            e_colors[key] = e_color
            e_times[key] = e_time
            labels[key] = label

    for k in graphv.keys():
        draw_graphs(graphv[k], k)

    conn.close()
 
    return graphs, labels, e_colors, e_times

def draw_graphs(graph, output_fn):
    g = graph[0]
    label = graph[1]
    e_color = graph[2]
    e_time = graph[3]
 
    deg = g.degree_property_map("in")
    ebet = betweenness(g)[1]
    pos = arf_layout(g, max_iter=0)

    graphviz_draw(g,size = (20,10), vprops={"xlabel":label, "labeldistance" : 50, "fontsize":15 },\
        eorder = ebet, vorder = deg, ecolor = e_color, eprops = {"dir": 'forward', "arrowsize":1}, penwidth = e_time, \
        output= "graphs/" + output_fn + ".pdf")

    return

if __name__ == '__main__':
    if len(sys.argv) == 2:
        testcase = sys.argv[1]
        generate_graphs(testcase)
    else:
        print "%s {testcase}" % (sys.argv[0])
        exit(0)
