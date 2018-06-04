#!/bin/bash

for VNF in `virsh list --all | awk '{print $2}' | grep -v "Name" | sed '/^\s*$/d'`
do
	echo $VNF
	virsh shutdown $VNF 2> /dev/null > /dev/null
	sleep 1
done
