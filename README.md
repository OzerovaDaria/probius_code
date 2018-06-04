# Introduction
- Probius: Automated Approach for VNF and Service Chain Analysis in Software-Defined NFV  

# Notification
- If you find any bugs or have some questions, please send an e-mail to us.  

# Configuration
- The configuration of the Probius system: config/analysis.conf  
- The configurations of VNFs: config/vnf.conf  
- The service chain policies: config/policy.conf  

# Test environment
- The current Barista is fully tested on Ubuntu 14.04/16.04.  
- It may work on other Linux platforms if its dependency issues are solved.  

# Compilation
1. Move to the setup directory  
$ cd kvm  
2. Install dependencies (ubuntu 14.04/16.04)  
$ ./deps_ubuntu(14/16).sh  
3. Install KVM and Open vSwitch  
$ ./install.sh  
4. Reboot  
$ sudo reboot  
5. Move to the setup directory again  
$ cd kvm  
6. Configure KVM networks (Management network: 192.168.254.0/24)  
$ ./configure.sh  

# Execution
- Analyze single VNFs  
$ ./analysis.py vnf  
- Analyze service chains with the specific number of VNFs  
$ ./analysis.py sc [# of VNFs]  
- Analyze a specific service chain  
$ ./analysis.py case [VNF1,VNF2,VNF3,...]  
- Detect performance anomaly  
$ ./anomaly.py  
- Draw state transition graphs for a suspicious service chain  
$ ./graph.py [VNF1,VNF2,VNF3, ...]  
- Get the details of a suspicious service chain  
$ ./report.py [VNF1,VNF2,VNF3, ...]  

# Author
- Jaehyun Nam <namjh@kaist.ac.kr>  

# Contributor
- Junsik Seo <js0780@kaist.ac.kr>  
