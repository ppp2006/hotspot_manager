#!/usr/bin/env python
# -*- coding:utf-8 -*-
from mod_python import apache
from urllib import unquote
import os
import sys
import os.path

def get_wlan_interface():
    f = open('/proc/net/wireless', 'r')
    for line in f:
        if line.find('wlan') != -1:
            return line.split(':')[0].lstrip()

def get_scripts_path():
    apache_conf = open('/etc/apache2/apache2.conf', 'r')

    for line in apache_conf:
        line = line.rstrip()  #remove \n
        if line.find('scripts') != -1:
            return line.split(' ')[-1].rstrip('>')
    return ''

def handler(req):
    reload(sys) #set default encoding from ascii to utf-8
    sys.setdefaultencoding('utf-8')

    apache.log_error(req.args)

    params = {}
    for pair in req.args.split('&'):
        key, value = pair.split('=')
        params[key] = value
    ssid = params['ssid']
    password = params['passwd']
    req.content_type = "text/plain; charset=utf-8"
    req.write('开始连接wifi咯！')

    scripts_path = get_scripts_path()
    if scripts_path == '':
        apache.log_error('scripts_path resolv failed!')
    catkin_ws = scripts_path.split('src')[0]
    sys.path.append(catkin_ws+'devel/lib/python2.7/dist-packages')
    sys.path.append('/opt/ros/hydro/lib/python2.7/dist-packages')
    os.environ['ROS_MASTER_URI'] = 'http://localhost:11311'
    import rospy
    from qbo_config_manager.srv import *
    rospy.wait_for_service('/config_connect_user_wifi')
    proc = rospy.ServiceProxy('/config_connect_user_wifi', ConnectWifi)
    result = proc(ssid, 'p'+password)  #ROS 把'123456'理解成数字，而不是字符串，所以要在前面加字母占位符

    return apache.OK

