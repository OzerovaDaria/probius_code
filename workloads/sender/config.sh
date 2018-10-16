#!/bin/bash

INTERFACE="enp12s0"
IP_ADDR=`ifconfig $INTERFACE | grep "inet addr" | awk '{print $2}' | awk -F":" '{print $2}'`

RECEIVER_NET="192.168.10.0"
SENDER_IP="192.168.10.10"
SENDER_GW="192.168.10.1"
