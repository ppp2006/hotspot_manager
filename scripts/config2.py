#!/usr/bin/env python
# -*- coding:utf-8 -*-
from urllib import unquote
import os
import os.path
import sys
import subprocess
import cherrypy
import roslib
import rospy
from qbo_config_manager.srv import *
from robot_util import *

#web server!!!
class ConfigManager(object):
    @cherrypy.expose
    def index(self):
        f = open('index.html')
        buf = f.read()
        f.close()
        return buf
    @cherrypy.expose
    def connect(self, ssid, password):
        print 'cherrypy recv wifi : ' + ssid + ' ' + password
        rospy.wait_for_service('/config_connect_user_wifi')
        proc = rospy.ServiceProxy('/config_connect_user_wifi', ConnectWifi)
        result = proc(ssid, 'p'+password)  #ROS 把'123456'理解成数字，而不是字符串，所以要在前面加字母占位符
        if (result.result):
            return '连接成功！'
        else:
            return '连接失败！'

if __name__ == "__main__":
    cwd = get_scripts_path()
    os.chdir(cwd)
    #web server!!!
    cherrypy.quickstart(ConfigManager())


