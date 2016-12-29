from django import template
from app import kubernetes_api, jenkins_api
from django.contrib.sessions.models import Session
import time
import re

register = template.Library()


@register.filter(name="get_list_data")
def get_list_data(n, array):
    return array[n]


@register.filter(name="get_namespaces")
def get_namespaces(n):
    html = ''
    for namespace in  kubernetes_api.get_namespaces():
        html += """      <li><a href="/namespaces/?change_n=%s"><i class="glyphicon glyphicon-unchecked"></i> %s</a></li>\n"""%(namespace,namespace)
    return html

@register.filter(name="get_session_value")
def get_session_value(key):
    s = Session.objects.get()
    d = s.get_decoded()
    if d.has_key(key):
        return s.get_decoded()[key]
    else:
        return "no key: %s"%(str(key))

@register.filter(name="get_cst_time")
def get_cst_time(date_str):
    m = re.match("(\d+-\d+-\d+)T(\d+:\d+:\d+).*",date_str)
    if m:
        date_str = "%s %s"%(m.group(1),m.group(2))
        timeArray = time.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        timeStamp = int(time.mktime(timeArray))
        timeStamp_shanghai = timeStamp + 3600 * 8
        return time.strftime('%Y-%m-%d %H:%M',time.localtime(timeStamp_shanghai))
    else:
        return "00:00:00 00:00:00"

@register.filter(name="get_latest_build_number")
def get_latest_build_number(item_name):
    return jenkins_api.get_lastbuild_number(item_name)


@register.filter(name="get_latest_build_re")
def get_latest_build_re(item_name):
    return jenkins_api.get_build_status_result(item_name,get_latest_build_number(item_name))


@register.filter(name="get_using_version")
def get_using_version(rc_namespace):
    m = re.match("(.*)\((.*)\)", rc_namespace)
    if m:
        rc = m.group(1)
        namespace = m.group(2)
    else:
        return 'Get version error'
    data = kubernetes_api.get_one_replicationcontroller(namespace, rc)
    image_url = data['spec']['template']['spec']['containers'][0]['image']
    m = re.match(".*:(.*)",image_url)
    if m:
        return m.group(1)
    else:
        return 'Get version error'

@register.filter(name="is_or_not_in_building")
def is_or_not_in_building(item_name):
    return jenkins_api.is_or_not_in_building(item_name, int(get_latest_build_number(item_name)))


@register.filter(name="return_build_button")
def return_build_button(item_name):
    if not is_or_not_in_building(item_name):
        return """<a href="/build_image/?action=build_image&item_name=%s"><button type="button" class="btn btn-outline btn-info">Build</button></a>""" % item_name
    else:
        return """<a href="#"><button type="button" class="btn btn-info disabled">Building</button></a>"""
