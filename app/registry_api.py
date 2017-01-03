#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
author = 'Perling'
mail   = 'linsmiling@sina.cn'
time   = '2016/12/19'
"""

import sys
reload(sys)
sys.setdefaultencoding('utf8')


import urllib2
import json

registry="54.223.166.145:5000"
private="172.31.14.229:5000"
registry_url = "http://%s"%registry


def http_get(url):
    req = urllib2.Request(url)
    req.add_header("Content-Type","application/json-rpc")
    resp = urllib2.urlopen(req)
    resp_json = json.loads(resp.read())
    return resp_json

def get_repository_list():
    data = http_get(registry_url+"/v2/_catalog")
    repository_list = data['repositories']
    return repository_list

def get_repository_tags(repository):
    data = http_get("%s/v2/%s/tags/list"%(registry_url,repository))
    tags = data['tags']
    return tags

def get_all_repository_tags():
    data = {}
    for repositoary in get_repository_list():
        data[repositoary]=get_repository_tags(repositoary)
    return data

def get_tag_create_time(repository_name,tag):
    data = http_get("%s/v2/%s/manifests/%s"%(registry_url,repository_name,tag))
    date_str = json.loads(data['history'][0]['v1Compatibility'])['created']
    return date_str

def get_tag_digest(repository_name,tag):
    url = "%s/v2/%s/manifests/%s"%(registry_url,repository_name,tag)
    req = urllib2.Request(url)
    req.get_method = lambda: 'HEAD'
    resp = urllib2.urlopen(req)
    return resp.headers['Docker-Content-Digest']

def delete_tag(repository_name,tag):
    tag_digest = get_tag_digest(repository_name,tag)
    url = "%s/v2/%s/manifests/%s"%(registry_url,repository_name,tag_digest)
    req = urllib2.Request(url)
    req.get_method = lambda: 'DELETE'
    try:
        resp = urllib2.urlopen(req)
        return True
    except urllib2.URLError, e:
        print e.reason
        return False

print get_repository_tags("trading/trading-merge")[-10:]