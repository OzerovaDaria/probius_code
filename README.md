# Introduction
- Probius: Automated Approach for VNF and Service Chain Analysis in Software-Defined NFV  

# Notification
- If you find any bugs or have some questions, please send an e-mail to us.  

# Configuration
- The configuration of the Probius system: config/analysis.conf  
- The configurations of VNFs: config/vnf.conf  
- The service chain policies: config/policy.conf  

# Test environment
- The current Probius is fully tested on Ubuntu 16.04.  
- It may work on other Linux platforms if its dependency issues are solved.  

# Requirement
- Psutil version = 1.2.1  

# Compilation
0. Set up a KVM environment (Management network: 192.168.254.0/24)  
$ git clone htps://github.com/sdx4u/kvm  
1. Get the source codes of Probius  
$ cd ~  
$ git clone https://github.com/sdx4u/probius  
2. Move to the setup directory  
$ cd ~/probius/setup/kvm  
3. Install dependencies  
$ ./deps_ubuntu16.sh  
5. Reboot  
$ sudo reboot  

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
