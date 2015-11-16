#!/usr/bin/env python
# -*- coding:utf-8 -*-
import os
import os.path
import time
import subprocess
import pexpect

ROOT_PASSWD = 'runji'
PACKAGE_NAME = 'qbo_config_manager'

def get_scripts_path():
    s = subprocess.check_output(['rospack', 'find', PACKAGE_NAME])
    path = os.path.join(s.rstrip(), 'scripts')
    return path

def expect_run(cmd):
    TIME_OUT = 20 #单位：秒
    p = pexpect.spawn(cmd)
    p.logfile = open('/tmp/e.log', 'w')
    if p.expect(['.*password.*']) == 0:
        p.sendline(ROOT_PASSWD)
        time.sleep(1)
        p.expect(pexpect.EOF, TIME_OUT)
    else:
        raise AssertionError("Fail to exec %s!"%cmd)

