#coding=utf-8
import os
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseNotFound
from django.conf import settings
from functools import wraps
from django.utils.decorators import available_attrs
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models.base import ModelBase
from helpdesk.models import HelpDeskUser, Application
from message.models import Mail
from string import join

def is_alloter():
    def decorator(view_func):
        @wraps(view_func, assigned=available_attrs(view_func))
        def _wrapped_view(request, *args, **kwargs):
            r = HelpDeskUser.objects.filter(user = request.user, role='1')
            if r.exists():
                return view_func(request, *args, **kwargs)
            return HttpResponse('权限不足！')
        return _wrapped_view
    return decorator

def is_applicant():
    def decorator(view_func):
        @wraps(view_func, assigned=available_attrs(view_func))
        def _wrapped_view(request, *args, **kwargs):
            r = HelpDeskUser.objects.filter(user = request.user, role='0')
            if r.exists():
                return view_func(request, *args, **kwargs)
            return HttpResponse('权限不足！')
        return _wrapped_view
    return decorator

def is_operator():
    def decorator(view_func):
        @wraps(view_func, assigned=available_attrs(view_func))
        def _wrapped_view(request, *args, **kwargs):
            r = HelpDeskUser.objects.filter(user = request.user, role='2')
            if r.exists():
                return view_func(request, *args, **kwargs)
            return HttpResponse('权限不足！')
        return _wrapped_view
    return decorator

def is_staff():
    def decorator(view_func):
        @wraps(view_func, assigned=available_attrs(view_func))
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_staff==True:
                return view_func(request, *args, **kwargs)
            return HttpResponse('权限不足！')
        return _wrapped_view
    return decorator


def get_role(request):
    dicts = {}
    if str(request.user) != 'AnonymousUser':
        if HelpDeskUser.objects.filter(user=request.user, role='0').exists():
            dicts['is_applicant'] = True
        if HelpDeskUser.objects.filter(user=request.user, role='1').exists():
            dicts['is_alloter'] = True
        if HelpDeskUser.objects.filter(user=request.user, role='2').exists():
            dicts['is_operator'] = True
    return dicts






def get_template(template):
    path = settings.BASE_DIR + "/helpdesk/templates/" + template
    if os.path.isfile(path):
        return template
    tmp = template.split('/', 1)
    if len(tmp) > 1:
        return 'apply/%s' % tmp[1]
    return template

def get_admin_email():
    if settings.DEBUG:
        return settings.ADMINS[0][1]

    alloters = HelpDeskUser.objects.filter(role = '1')
    receiver = []
    for a in alloters:
        if a.email.strip() != '':
            receiver.append(a.email)
    return receiver

def send_mail(request, o, template, receiver,subject=None,attachs=None):
    mail = Mail()
    mail.creator = request.user.username
    mail.receiver = join(receiver,', ')
    mail.attach = attachs
    if subject == None:
        mail.subject = u'HelpDesk通知'
    else:
        mail.subject = subject
    from  django.template.loader  import  get_template as dj_get_template
    from django.template import Context
    t = dj_get_template(template)
    dicts = {
        'o':o, 
        'request':request,
        'mail_info': '%s/mail_info.html' % o.get_short_category()
        }
    mail_finish = '%s/mail_finish.html' % o.get_short_category()
    path = settings.BASE_DIR + "/helpdesk/templates/" + mail_finish
    if os.path.isfile(path):
        dicts['mail_finish'] = mail_finish
    mail.content = t.render(Context(dicts))

    try:
        mail.save()
    except:
        return False

    mail.send(request.user)
    return True

def fake_send_mail(request, o, template, receiver, subject=None):
    from  django.template.loader  import  get_template 
    from django.template import Context
    t = get_template(template)
    content = t.render(Context({'o':o, 'request':request}))
    return HttpResponse(content)


def get_apply_category(): 
    from . import models
    dic = {}
    for item in models.__dict__.items():
        if type(item[1]) == ModelBase and item[1].__module__ == models.__name__:
            if len(item[0]) > 11 and item[0][-11:] == 'Application':
                c = item[0][:-11].lower()
                if os.path.isfile('%s/views/apply_%s.py' % (os.path.dirname(__file__), c)):
                    dic[c] = {
                        'tag': item[0],
                        'model': item[1],
                        'name': item[1]._meta.verbose_name
                    }
    return dic
APPLICATION_CATEGORIES = get_apply_category()

def get_apply_category_list():
    from . import models
    import re
    
    dic = APPLICATION_CATEGORIES

    fname = models.__file__
    if fname[-4:] == '.pyc':
        fname = fname[:-1]
    if fname[-3:] == '.py':
        f = open(fname)
        line = f.readline()
        lis = []
        while line:
            res = re.findall(r'^\s*class\s+(?P<tag>\w+)Application', line)
            if res and dic.has_key(res[0].lower()):
                obj = dic[res[0].lower()]
                obj['short_tag'] = res[0].lower()
                lis.append(obj)
            line = f.readline()
    else:
        lis = []
        for k, v in dic.items():
            v['short_tag'] = k
        lis.append(v)
    return lis
APPLICATION_CATEGORIES_LIST = get_apply_category_list()


def get_apply_views():
    dic = {}
    for k in APPLICATION_CATEGORIES.keys():
        if settings.DEBUG:
            myview = __import__('helpdesk.views.apply_%s'%k, {}, {}, ['apply_%s'%k])
            dic[k] = getattr(myview, '%sApplyView' % k.capitalize())
        else:
            try:
                myview = __import__('helpdesk.views.apply_%s'%k, {}, {}, ['apply_%s'%k])
                dic[k] = getattr(myview, '%sApplyView' % k.capitalize())
            except Exception,e:
                continue
    return dic
APPLICATION_VIEWS = get_apply_views() 