# -*- coding: utf-8 -*-

import sys
reload(sys)
sys.setdefaultencoding('utf8')
import urllib2
import json

kubernetes_apiserver = 'http://54.223.166.145:8081/api/v1'
kubernetes_exten_apiserver = 'http://54.223.166.145:8081/apis/extensions/v1beta1'

def http_get(url):
    req = urllib2.Request(url)
    resp = urllib2.urlopen(req)
    response = resp.read()
    try:
        resp_json = json.loads(response)
        return resp_json
    except Exception, e:
        print Exception, e
        return response


def http_post(url, post_data):
    post_data = json.dumps(post_data)
    req = urllib2.Request(url, post_data)
    resp = urllib2.urlopen(req)
    resp_json = json.loads(resp.read())
    return resp_json


def get_nodes():
    data = http_get(kubernetes_apiserver + "/nodes")
    return data


def get_namespaces():
    data = http_get(kubernetes_apiserver + "/pods")
    namespaces = []
    for item in data['items']:
        if not item['metadata']['namespace'] in namespaces:
            namespaces.append(item['metadata']['namespace'])
    return namespaces


def get_pods(namespace):
    if namespace == 'All':
        data = http_get(kubernetes_apiserver + "/pods")
    else:
        data = http_get(kubernetes_apiserver + "/namespaces/%s/pods" % namespace)
    return data


def get_pod_log(namespace, podname):
    if namespace == 'All':
        pods_info = http_get(kubernetes_apiserver + "/pods")
        for pod in pods_info['items']:
            if pod['metadata']['name'] == podname:
                namespace = pod['metadata']['namespace']
                break
    data = http_get(kubernetes_apiserver + "/namespaces/%s/pods/%s/log?tailLines=100&pretty=json" % \
                    (namespace, podname)
                    )
    print namespace
    print data
    return data


def get_replicationcontroller(namespace):
    if namespace == 'All':
        data = http_get(kubernetes_apiserver + "/replicationcontrollers")
    else:
        data = http_get(kubernetes_apiserver + "/namespaces/%s/replicationcontrollers" % namespace)
    return data


def get_one_replicationcontroller(namespace, rc):
    data = http_get(kubernetes_apiserver + "/namespaces/%s/replicationcontrollers/%s" % (namespace, rc))
    return data


def update_deployment(namespace, dm, image):
    data = [
        {
            "op" : "replace",
            "path" : "/spec/template/spec/containers/0/image",
            "value" : image
        },
        {
            "op" : "replace",
            "path" : "/spec/strategy/type",
            "value" : "RollingUpdate"
        }
    ]
    post_data = json.dumps(data)
    #url = "http://54.223.166.145:8081/apis/extensions/v1beta1/namespaces/trading/deployments/merger"
    url = "%s/namespaces/%s/deployments/%s" % (kubernetes_exten_apiserver, namespace, dm)
    req = urllib2.Request(url, post_data)
    req.get_method = lambda: 'PATCH'
    req.add_header("Content-Type","application/json-patch+json")
    resp = urllib2.urlopen(req)
    return resp.read()


def get_deployment(namespace):
    if namespace == 'All':
        data = http_get(kubernetes_exten_apiserver + "/deployments")
    else:
        data = http_get(kubernetes_exten_apiserver + "/namespaces/%s/deployments" % namespace)
    return data


def get_one_deployment(namespace, dm):
    data = http_get(kubernetes_exten_apiserver + "/namespaces/%s/deployments/%s" % (namespace, dm))
    return data
