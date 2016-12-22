# coding=utf8
from __future__ import division
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
import kubernetes_api
import registry_api
import sys
reload(sys)
sys.setdefaultencoding('utf8')


def login_auth(request):
    if request.method == 'GET':
        if 'logut' in request.GET:
            logout(request)
            return HttpResponseRedirect("/accounts/login/")
        else:
            return render(request, 'login.html')
    elif request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                request.session['username'] = username
                request.session['namespace'] = 'default'
                if 'next' in request.GET:
                    return HttpResponseRedirect(request.GET['next'])
                else:
                    return HttpResponseRedirect("/index/")
            else:
                messages.info(request, "用户没有被激活")
                return HttpResponseRedirect("/accounts/login/")
        else:
            messages.info(request, "用户不存在或者密码错误")
            return HttpResponseRedirect("/accounts/login/")


@login_required()
def index(request):
    return render(request, 'index.html')


@login_required()
def nodes(request):
    data = kubernetes_api.get_nodes()
    return render(request, 'nodes.html', {'data': data['items']})


@login_required()
def namespaces(request):
    if 'change_n' in request.GET:
        change_namespace = request.GET['change_n']
        all_namespace = kubernetes_api.get_namespaces()
        all_namespace.append('All')
        if change_namespace in all_namespace:
            request.session['namespace'] = change_namespace
            messages.success(request, '已将默认Namespace切换为 %s' % change_namespace)
        else:
            messages.error(request, 'No Namespace : %s' % change_namespace)
        return HttpResponseRedirect(request.META['HTTP_REFERER'])


@login_required()
def repository(request):
    if 'action' in request.GET and request.GET['action'] == 'list_tags':
        repository = request.GET['repository']
        list_ = registry_api.get_repository_tags(repository)
        data = {}
        for tag in list_ :
            data[tag] = registry_api.get_tag_create_time(repository, tag)
        return render(request, 'repository_manage.html', {'data': data, 'repository': repository})
    elif 'action' in request.GET and request.GET['action'] == 'delete_tag':
        repository = request.GET['repository']
        tag = request.GET['tag']
        if registry_api.delete_tag(repository, tag):
            messages.success(request, "删除%s的版本%s成功" % (repository, tag))
            return HttpResponseRedirect(request.META['HTTP_REFERER'])
        else:
            messages.info(request, "删除%s的版本%s失败" % (repository, tag))
            return HttpResponseRedirect(request.META['HTTP_REFERER'])
    else:
        info = registry_api.get_all_repository_tags()
        data = {}
        for key, value in info.items():
            data[key] = len(value)
        return render(request, 'repository.html', {'data': data})


@login_required()
def pods(request):
    if 'action' in request.GET and request.GET['action'] == 'list_pods':
        namespace = request.session['namespace']
        info = kubernetes_api.get_pods(namespace)
        data = []
        for pod in info['items']:
            p = {}
            p['name'] = pod['metadata']['name']
            p['labels'] = pod['metadata']['labels']
            p['startTime'] = pod['status']['startTime']
            p['nodeName'] = pod['spec']['nodeName']
            p['podIP'] = pod['status']['podIP']
            p['phase'] = pod['status']['phase']
            p['container_num'] = len(pod['status']['containerStatuses'])
            p['images'] = ''
            for con in pod['status']['containerStatuses']:
                p['images'] += "%s</br>" % con['image']
            data.append(p)
        return render(request, 'pods.html', {'data': data})