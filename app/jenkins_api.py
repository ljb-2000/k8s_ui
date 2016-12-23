#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
author = 'Perling'
mail   = 'linsmiling@sina.cn'
time   = '2016/12/20'
"""

import jenkins
import sys
reload(sys)
sys.setdefaultencoding('utf8')


server = jenkins.Jenkins('http://54.223.166.145:8085', username='admin', password='851750618')


def build_image(item_name):
    result = server.build_job(item_name)
    return result


def get_build_console_log(item_name, build_number):
    return server.get_build_console_output(item_name, build_number)


def is_or_not_in_building(item_name, build_number):
    print "-s-"
    print server.get_build_info(item_name, build_number)['building']
    print "-e-"
    return server.get_build_info(item_name, build_number)['building']


def get_lastbuild_number(item_name):
    return server.get_job_info(item_name)['lastBuild']['number']


def get_build_status_result(item_name, build_number):
    return server.get_build_info(item_name, build_number)['result']


def get_all_jobs():
    return server.get_all_jobs()


print is_or_not_in_building('trading-merge', 43)


#print get_all_jobs()
#print build_image('trading-merge')
#print is_or_not_in_building('trading-merge',40)