from django import template
from app import kubernetes_api
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

