#!/bin/bash
MODE=$1
WLAN_PATH=/sys/class/net/
pkill dnsmasq
pkill hostapd
pkill wpa_supplicant
pkill dhclient

if [ $MODE == "AP" ]; then
ifdown --force -i $AP_INTF_FILE $WLAN_INTF
fi

#卸载网卡驱动
if [ $WLAN_CARD == 'RealTek' ]; then
    modprobe -r 8188eu
else
    modprobe -r iwldvm iwlwifi
fi
#确认网卡在sysfs已删除
while true; do
    echo "waiting for $WLAN_INTF delete..."
    sleep 1
    if [ ! -e $WLAN_PATH$WLAN_INTF ]; then
        echo "$WLAN_INTF deleted!"
        break
    fi
done
#安装网卡驱动
if [ $WLAN_CARD == 'RealTek' ]; then
    modprobe 8188eu
else
    modprobe iwlwifi iwldvm
fi
#确认网卡在sysfs已创建
while true; do
    echo "waiting for $WLAN_INTF created..."
    sleep 1
    if [ -e $WLAN_PATH$WLAN_INTF ]; then
        echo "$WLAN_INTF created!"
        break
    fi
done

if [ $MODE == "AP" ]; then
ifup -i $AP_INTF_FILE $WLAN_INTF
fi

#above op are preface

if [ $MODE == "AP" ]; then
hostapd -B $HOSTAPD_CONF_FILE
dnsmasq -i $WLAN_INTF -K --dhcp-range=$DHCP_RANGE_CONF
fi

if [ $MODE == "STA" ]; then
wpa_supplicant -B -i$WLAN_INTF -Dwext -c $WPA_CONF_FILE
dhclient $WLAN_INTF 
fi
