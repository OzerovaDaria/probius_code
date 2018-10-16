#!/bin/bash

if [ -z $1 ]
then
	echo "Usage: $0 [VNF name] [e1000 | virtio]"
elif [ -z $2 ]
then
	echo "Usage: $0 [VNF name] [e1000 | virtio]"
elif [ "$2" == "e1000" ]
then
	sudo cat /etc/libvirt/qemu/$1.xml > $1.xml
	sed -i "s/<model type='virtio'\/>/<model type='e1000'\/>/g" $1.xml
	virsh define $1.xml > /dev/null
	rm $1.xml
elif [ "$2" == "virtio" ]
then
	sudo cat /etc/libvirt/qemu/$1.xml > $1.xml
	sed -i "s/<model type='e1000'\/>/<model type='virtio'\/>/g" $1.xml
	virsh define $1.xml > /dev/null
	rm $1.xml
fi
