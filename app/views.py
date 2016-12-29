# coding=utf8
from __future__ import division
from django.shortcuts import render,HttpResponse
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from models import Project, Image, Repository
import kubernetes_api , registry_api , jenkins_api
import json

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
    if request.method == 'GET':
        if 'action' in request.GET and request.GET['action'] == 'list_tags':
            repository = request.GET['repository']
            list_ = registry_api.get_repository_tags(repository)
            data = {}
            for tag in list_:
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
            data = []
            js_id = 0
            for key, value in info.items():
                r = {}
                r['name'] = key
                r['len'] = len(value)
                js_id += 1
                r['js_id'] = "t-%d" % js_id
                f_re = Repository.objects.filter(name=key)
                if len(f_re) >= 1:
                    r['description'] = f_re[0].description
                    r['category'] = f_re[0].category
                else:
                    r['description'] = ''
                    r['category'] = ''
                data.append(r)
            return render(request, 'repository.html', {'data': data})
    else:
        category = request.POST['category']
        description = request.POST['description']
        repository = request.POST['name']
        f_re = Repository.objects.filter(name = repository)
        if len(f_re) >= 1:
            f_re.update(category=category, description=description)
        else:
            f_re.create(name=repository, category=category, description=description)
        Repository.objects.update_or_create(name=repository, category=category, description=description, defaults={'name': repository})
        messages.success(request, "%s saved success" % repository)
        return HttpResponseRedirect(request.META['HTTP_REFERER'])


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
    elif 'action' in request.GET and request.GET['action'] == 'pod_log':
        namespace = request.GET['namespace']
        podname = request.GET['podname']
        data = kubernetes_api.get_pod_log(namespace, podname)
        return HttpResponse("<pre>" + data + "</pre>")

@login_required()
def replicationcontroller(request):
    if 'name' in request.GET:
        name = request.GET['name']
        all_rc_info = kubernetes_api.get_replicationcontroller('All')
        for rc in all_rc_info['items']:
            if rc['metadata']['name'] == name:
                namespace = rc['metadata']['namespace']
                break
        else:
            namespace = 'default'
        decode_json  = kubernetes_api.get_one_replicationcontroller(namespace, name)
        json_former = json.dumps(decode_json)
        return render(request, 'json-show.html', {'page_name': name, 'json_data': json_former})
    else:
        namespace = request.session['namespace']
        info = kubernetes_api.get_replicationcontroller(namespace)
        data = []
        for rc in info['items']:
            r = {}
            r['readyReplicas'] = rc['status']['readyReplicas']
            r['replicas'] = rc['status']['replicas']
            r['selector'] = rc['spec']['selector']
            r['name'] = rc['metadata']['name']
            r['creationTimestamp'] = rc['metadata']['creationTimestamp']
            data.append(r)
        return render(request, 'rc.html', {'data': data})


@login_required()
def project(request):
    if request.method == 'POST':
        name = request.POST['name']
        use_rc = request.POST['use_rc']
        jenkins_job_name = request.POST['jenkins_job_name']
        description = request.POST['des']
        if Project.objects.create(name = name, use_rc = use_rc, jenkins_job_name = jenkins_job_name, description = description):
            messages.success(request, "Create project %s success" % name)
        else:
            messages.error(request, "Create project %s failed" % name)
        return HttpResponseRedirect(request.META['HTTP_REFERER'])
    if request.method == 'GET':
        if request.GET['action'] == 'list_project':
            data = Project.objects.all()
            all_rc_info = kubernetes_api.get_replicationcontroller('All')
            rcs = []
            for rc in all_rc_info['items']:
                rcs.append("%s (%s)" % (rc['metadata']['name'], rc['metadata']['namespace']))
            return render(request, 'project.html', {'data': data, 'rcs': rcs, 'all_jenkins_jobs': jenkins_api.get_all_jobs()})
        if request.GET['action'] == 'delete':
            delete_pro_id = request.GET['d_id']
            p = Project.objects.filter(id=delete_pro_id)
            project_name = p[0].name
            if p:
                messages.success(request, "Delete project %s success" % (project_name))
                p.delete()
            else:
                messages.warning(request, "Delete project %s failed, No project named %s" % (project_name, project_name))
        return HttpResponseRedirect(request.META['HTTP_REFERER'])


@login_required()
def jenkins(request):
    if request.GET['action'] == 'build_image':
        item_name = request.GET['item_name']
        jenkins_api.build_image(item_name)
        messages.info(request, "Start build %s" % item_name)
        return HttpResponseRedirect(request.META['HTTP_REFERER'])