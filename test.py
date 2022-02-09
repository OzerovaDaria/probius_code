import psutil

for process in psutil.process_iter():
    vnf = process.as_dict(attrs=['name', 'pid', 'cmdline'])
    for entry in vnf['cmdline']:
        for entry in vnf['cmdline']:
#            print("ENTRY = ", entry)
            if "id=net" in entry:
                print("ENTRY = ", entry)
                options = entry.split(",")

                id_option = options[2]
                net_id = id_option.split("=")[1]
                print("NETID = ", net_id)

                mac_option = options[3]
                mac = mac_option.split("=")[1]
                print("MAC = ", mac)
