#!/bin/bash

DIRECTORY=`dirname $0`
. $DIRECTORY/config.sh

sudo pkill -9 iperf3 2> /dev/null

if [ "$IP_ADDR" != "$SENDER_IP" ]
then
	sudo ifconfig $INTERFACE down 2> /dev/null
	sleep 1
	sudo ifconfig $INTERFACE $SENDER_IP netmask 255.255.255.0 up 2> /dev/null
	sleep 1
fi

sudo ip route add $RECEIVER_NET/24 via $SENDER_GW 2> /dev/null
sleep 1
