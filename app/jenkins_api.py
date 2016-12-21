#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
author = 'Perling'
mail   = 'linsmiling@sina.cn'
time   = '2016/12/20'
"""

import sys
reload(sys)
sys.setdefaultencoding('utf8')
import jenkins

server = jenkins.Jenkins('http://54.223.166.145:8085', username='admin', password='851750618')

user = server.get_whoami()





print user['fullName']
print server.get_all_jobs()

print server.get_build_info('mobile.gu360.com',31)