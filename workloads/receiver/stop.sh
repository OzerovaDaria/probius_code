#!/bin/bash

DIRECTORY=`dirname $0`
. $DIRECTORY/config.sh

sudo pkill -9 iperf3 2> /dev/null

if [ -z $1 ] # normal
then
	if [ "$IP_ADDR" != "$RECEIVER_IP" ] # NAT IP address
	then
		sudo ifconfig $INTERFACE down 2> /dev/null
		sleep 1
		sudo ifconfig $INTERFACE $RECEIVER_IP netmask 255.255.255.0 up 2> /dev/null
		sleep 1
	fi
else # NAT
	if [ "$IP_ADDR" != "$RECEIVER_NAT_IP" ] # normal IP address
	then
		sudo ifconfig $INTERFACE down 2> /dev/null
		sleep 1
		sudo ifconfig $INTERFACE $RECEIVER_NAT_IP netmask 255.255.255.0 up 2> /dev/null
		sleep 1
		sudo ip route add $SENDER_NET/24 via $RECEIVER_NAT_GW 2> /dev/null
		sleep 1
	fi
fi
