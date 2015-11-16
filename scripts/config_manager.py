#!/usr/bin/env python
# -*- coding:utf-8 -*-
import os
import os.path
import sys
import roslib
import rospy
import subprocess
import signal
import cherrypy
from qbo_config_manager.srv import *
from robot_util import *

SUB_DIR = 'gen'
SUB_NET_NUM = 8
DHCP_LEASE_HOUR = 2

def get_wlan_interface():
    nics = os.listdir('/sys/class/net')
    for nic in nics:
        if nic.startswith('wlan'):
            return nic
    raise AssertionError("wifi card find fail!")

def is_realtek_8188():
    for line in os.popen('lsmod'):
        if line.find('8188') != -1:
            return True
    return False

def generate_hostapd_conf(intf, apd_file_name):
    f = open(apd_file_name, 'w')
    # Basic configuration
    f.write('interface=%s\n'%intf)
    f.write('ssid=doudou\n')
    f.write('channel=1\n\n')
    # WPA and WPA2 configuration
    f.write('macaddr_acl=0\n')
    f.write('auth_algs=1\n')
    f.write('ignore_broadcast_ssid=0\n')
    f.write('wpa=3\n')
    f.write('wpa_passphrase=88888888\n')
    f.write('wpa_key_mgmt=WPA-PSK\n')
    f.write('wpa_pairwise=TKIP\n')
    f.write('rsn_pairwise=CCMP\n\n')
    # Hardware configuration
    if os.environ['WLAN_CARD'] == 'RealTek':
        f.write('driver=rtl871xdrv\n') #Realtek custum
        f.write('ieee80211n=1\n')
        f.write('hw_mode=g\n')
        f.write('device_name=RTL8192CU\n')
        f.write('manufacturer=Realtek\n')
    else:
        f.write('driver=nl80211\n') #Linux standard
        f.write('hw_mode=g\n')
    f.close()

def generate_AP_interfaces(intf, intf_file_name, sub_net_num):
    #prepare AP version of /etc/network/interfaces file
    f = open('/etc/network/interfaces','r')
    buf = f.read()
    f.close()
    f = open(intf_file_name, 'w')
    f.write(buf)
    f.write('\nauto %s\n'%intf)
    f.write('iface %s inet static\n'%intf)
    f.write('address 192.168.%s.1\n'%sub_net_num)
    f.write('netmask 255.255.255.0\n')
    f.write('gateway 192.168.%s.1\n'%sub_net_num)
    f.close()

def switch_to_ap(req):
    try:
        expect_run('sudo -E ./switch.sh "AP"')
        print 'AP doudou created'
        return True
    except Exception as e:
        print e
        print 'Error! AP doudou not created'
        return False

def connect_wifi(ssid=None, password=None):
    if ssid != None:
        intf = os.environ['WLAN_INTF']
        print 'ros node recv ssid : %s, password : %s'%(ssid, password)
        #return True #调试web server到ros node之间的通信开关
        wpa_file_name = os.environ['WPA_CONF_FILE']
        wpa_file = open(wpa_file_name, 'w')
        subprocess.call(['wpa_passphrase', ssid, password], stdout = wpa_file) # AP params -> PSK code
        wpa_file.close()
    try:
        expect_run('sudo -E ./switch.sh "STA"')
        print 'external wifi connected'
        return True
    except Exception as e:
        print e
        print 'Error! external wifi not connected'
        return False

def connect_user_wifi(req):
    ssid = req.ssid.decode('utf-8')
    password = req.password[1:] #ROS 把'123456'理解成数字，而不是字符串，所以要在前面加字母占位符
    return connect_wifi(ssid, password)

def connect_last_wifi(req):
    return connect_wifi()

if __name__ == "__main__":
    #find scripts dir, chdir to it
    cwd = get_scripts_path()
    os.chdir(cwd)

    try:
        os.mkdir(SUB_DIR)
    except:
        pass
    intf_file_name = os.path.join(SUB_DIR, 'interfaces_AP')
    apd_file_name = os.path.join(SUB_DIR, 'hostapd.conf')
    wpa_file_name = os.path.join(SUB_DIR, 'wpa_supplicant.conf')
    #记录当前活动网卡名称
    intf = get_wlan_interface()
    #记录当前活动网卡品牌
    if is_realtek_8188():
        os.environ['WLAN_CARD'] = 'RealTek'
    else:
        os.environ['WLAN_CARD'] = 'Intel'
    #记录环境变量，用于给shell脚本传参
    os.environ['HOSTAPD_CONF_FILE'] = apd_file_name
    os.environ['AP_INTF_FILE'] = intf_file_name
    os.environ['WPA_CONF_FILE'] = wpa_file_name
    os.environ['WLAN_INTF'] = intf
    os.environ['DHCP_RANGE_CONF'] = 'interface:%s,192.168.%s.100,192.168.%s.109,%sh'%(intf, SUB_NET_NUM, SUB_NET_NUM, DHCP_LEASE_HOUR)
    #生成创建热点需要的配置文件
    generate_hostapd_conf(intf, apd_file_name)
    generate_AP_interfaces(intf, intf_file_name, SUB_NET_NUM)

    rospy.init_node('config_manager')
    #init switch to AP mode service
    s1 = rospy.Service('/config_switch_to_ap', Switch2AP, switch_to_ap)
    #init connect user wifi service
    s2 = rospy.Service('/config_connect_user_wifi', ConnectWifi, connect_user_wifi)
    #init connect last wifi service
    s3 = rospy.Service('/config_connect_last_wifi', ConnectLast, connect_last_wifi)

    rospy.spin()

