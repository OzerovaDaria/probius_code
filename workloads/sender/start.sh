#!/bin/bash

DIRECTORY=`dirname $0`
. $DIRECTORY/config.sh

if [ "$IP_ADDR" != "$SENDER_IP" ]
then
	sudo ifconfig $INTERFACE down 2> /dev/null
	sleep 1
	sudo ifconfig $INTERFACE $SENDER_IP netmask 255.255.255.0 up 2> /dev/null
	sleep 1
fi

sudo ip route add $RECEIVER_NET/24 via $SENDER_GW 2> /dev/null
sleep 1

if [ "$1" != "NAT" ]
then
	iperf3 -c $1 $2 $3 $4 $5 $6 $7 $8 -l 1K -t 0 2> /dev/null > /dev/null &
else
	iperf3 -c $2 $3 $4 $5 $6 $7 $8 $9 -l 1K -t 0 2> /dev/null > /dev/null &
fi
