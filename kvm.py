from proxmoxer import ProxmoxAPI

class KVM():
    def __init__(self, uuid=None):
        self.proxmox = None
        self.node = None
        self.password = None
        self.uuid = uuid
        self.log = []
        self.result = []

    def connect(self, hostname, nodename):
        self.proxmox = ProxmoxAPI(hostname, user='dzrlv@pve',
                              password='qwerty',
                              verify_ssl=False)
        for node in self.proxmox.nodes.get():
    	    for vm in self.proxmox.nodes(node['node']).qemu.get():
                #print(node['node'])
                print ("{0}. {1} => {2}".format(vm['vmid'], vm['name'], vm['status']))
        self.node = self.proxmox.nodes(nodename)
        #self.password = pwgen()

    def check_status(self, name):
        for node in self.proxmox.nodes.get():
            for vm in self.proxmox.nodes(node['node']).qemu.get():
                if vm['name'] == name:
                    if vm['status'] == "running":
                        return 1
                    else:
                        return 0

    def startvm(self, vmid=100):
        if self.isVMExist(vmid):
            self.node.qemu(vmid).status.start.post()
        #self.node.qemu(vmid).status.start.post()

    def stopvm(self, vmid=100):
        if self.isVMExist(vmid):
            self.node.qemu(vmid).status.stop.post()
        #self.isVMExist(vmid)
        #self.node.qemu(vmid).status.stop.post()

    def isVMExist(self, vmid=100):
        """
        Проверка на существование ВМ с указанным ID
        """
        result = False
        """
        for item in self.node.openvz.get():
            if item['vmid'] == str(vmid):
                result=True
        """
        for item in self.node.qemu.get():
            #print((item['vmid']), str(vmid), item['vmid'] == str(vmid))
            if str(item['vmid']) == str(vmid):
                result=True
        print(result)
        return result

    def task(self, tasks):
        """
        Пакетный режим
        """
        result = []
        flagerror = False
        for item in tasks:
            self.log.append(item)
            if item['action'] == 'connect':
                if self.connect(item['hostname'],
                     item['password'], item['node']):
                    result.append({'action': 'connect',
                        'status': 'error'})
                else:
                    result.append({'action': 'connect',
                        'status': 'error'})
            elif item['action'] == 'create':
                self.createstorage(vmid=int(item['vmid']),
                                   size=item['hdd'])
                self.create(vmid=int(item['vmid']),
                            hostname=item['hostname'],
                            mem=item['mem'],
                            cpus=item['cpu'])
                time.sleep(10)
                result.append({'action': 'create',
                    'status': 'ready'})
            elif item['action'] == 'delete':
                self.log.append('Удаление KVM ' + str(item['vmid']))
                self.deletevm(vmid=item['vmid'])
                time.sleep(10)
                self.log.append('Удалена KVM ' + str(item['vmid']))
                result.append({'action': 'delete',
                    'status': 'ready'})
            elif item['action'] == 'start':
                if 'args' in item.keys():
                    self.startvm(vmid=item['vmid'], args=item['args'])
                else:
                    self.startvm(vmid=item['vmid'])
                result.append({'action': 'start',
                    'status': 'ready'})
            elif item['action'] == 'stop':
                self.stopvm(vmid=item['vmid'])
                result.append({'action': 'stop',
                    'status': 'ready'})
            elif item['action'] == 'wait':
                time.sleep(300)
        if flagerror:
            return {'result': 'kvm', 'status': 'ready',
                'actions': result}
        else:
            return {'result': 'kvm', 'status': 'error',
                'actions': result}
"""
proxmoxx = KVM()
proxmoxx.connect("172.30.12.2", "w4")
for i in range(200, 212):
    if i != 208 and i != 209:
        proxmoxx.stopvm(i)

"""
