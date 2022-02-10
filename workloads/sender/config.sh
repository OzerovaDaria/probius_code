#!/bin/bash

INTERFACE="ens18"
print("CONFIG.SH Sender")
IP_ADDR=`ifconfig $INTERFACE | grep "inet addr" | awk '{print $2}' | awk -F":" '{print $2}'`
print(ifconfig $INTERFACE )
print(ifconfig $INTERFACE | grep "inet addr" )
print(ifconfig $INTERFACE | grep "inet addr" | awk '{print $2}' )
print("IP_ADDR = ", IP_ADDR)

RECEIVER_NET="192.168.10.0"
SENDER_IP="192.168.10.10"
SENDER_GW="192.168.10.1"
