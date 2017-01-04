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
import re
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
        print info
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
            p['container_id'] = pod['status']['containerStatuses']['containerID']
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
        return render(request, 'json-show.html', {'page_name': "Replicationcontrollers -----> %s" % name, 'json_data': json_former})
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
        use_dm = request.POST['use_dm']
        jenkins_job_name = request.POST['jenkins_job_name']
        description = request.POST['des']
        repository = request.POST['repository']
        if Project.objects.create(name = name, use_dm = use_dm, repository = repository, jenkins_job_name = jenkins_job_name, description = description):
            messages.success(request, "Create project %s success" % name)
        else:
            messages.error(request, "Create project %s failed" % name)
        return HttpResponseRedirect(request.META['HTTP_REFERER'])
    if request.method == 'GET':
        if request.GET['action'] == 'list_project':
            data = Project.objects.all()
            all_dm_info = kubernetes_api.get_deployment('All')
            dms = []
            for dm in all_dm_info['items']:
                dms.append("%s (%s)" % (dm['metadata']['name'], dm['metadata']['namespace']))
            repository = registry_api.get_repository_list()
            return render(request, 'project.html', {'data': data, 'dms': dms, "repository": repository , 'all_jenkins_jobs': jenkins_api.get_all_jobs()})
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
        elif request.GET['action'] == 'update':
            project_id = request.GET['pro_id']
            pro = Project.objects.filter(id=project_id)
            repository = pro[0].repository
            list_ = registry_api.get_repository_tags(repository)[-10:]
            data = {}
            for tag in list_:
                data[tag] = registry_api.get_tag_create_time(repository, tag)
            return render(request, 'deployment_update.html', {'data': data, 'repository': repository, 'pro_id': project_id} )


@login_required()
def jenkins(request):
    if request.GET['action'] == 'build_image':
        item_name = request.GET['item_name']
        jenkins_api.build_image(item_name)
        messages.info(request, "Start build %s" % item_name)
        return HttpResponseRedirect(request.META['HTTP_REFERER'])


@login_required()
def deployment(request):
    if request.method == 'GET':
        if 'name' in request.GET:
            name = request.GET['name']
            all_dm_info = kubernetes_api.get_deployment('All')
            for rc in all_dm_info['items']:
                if rc['metadata']['name'] == name:
                    namespace = rc['metadata']['namespace']
                    break
            else:
                namespace = 'default'
            decode_json  = kubernetes_api.get_one_deployment(namespace, name)
            json_former = json.dumps(decode_json)
            return render(request, 'json-show.html', {'page_name': "Deployments", 'json_data': json_former})
        elif 'action' in request.GET and request.GET['action'] == 'update':
            project_id = request.GET['pro_id']
            repository = request.GET['repository']
            tag = request.GET['tag']
            new_image = "%s/%s:%s" % (registry_api.private, repository, tag)
            pro = Project.objects.filter(id=project_id)
            dm_namespace = pro[0].use_dm
            m = re.match("(.*)\((.*)\)", dm_namespace)
            if m:
                dm = m.group(1)
                namespace = m.group(2)
            else:
                return 'Get version error'
            update_re = kubernetes_api.update_deployment(namespace, dm, new_image)
            messages.success(request, "Rolling Update start")
            return render(request, 'json-show.html', {'page_name': "%s Rolling Update Result" % dm,'json_data': update_re})
        else:
            namespace = request.session['namespace']
            info = kubernetes_api.get_deployment(namespace)
            print info
            data = []
            for dm in info['items']:
                r = {}
                r['replicas'] = dm['status']['replicas']
                r['availableReplicas'] = dm['status']['availableReplicas']
                r['updatedReplicas'] = dm['status']['updatedReplicas']
                r['name'] = dm['metadata']['name']
                r['creationTimestamp'] = dm['metadata']['creationTimestamp']
                data.append(r)
            return render(request, 'dm.html', {'data': data})
    else:
        new_scale = request.POST['new_scale']
        namespace = request.POST['namespace']
        dm = request.POST['dm']
        scale_re = kubernetes_api.deployment_scale(namespace, dm, new_scale)
        return render(request, 'json-show.html', {'page_name': "%s Rolling Update Result" % dm,'json_data': scale_re})