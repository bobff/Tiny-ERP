#coding=utf-8

import csv  
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseNotFound

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from dateutil.relativedelta import relativedelta
import simplejson
from  datetime import *
from helpdesk import is_alloter, is_applicant, is_operator, is_staff

from helpdesk.models import Application, HelpDeskUser,  ApplyType, Task, Package
from helpdesk import send_mail, get_role

from utils import render_to_response
from math import *

@login_required
@is_alloter()
def apply(request):
    days = request.GET.get('days', 90)
    days = int(days)
    if not days or days < 5:
        days = 30
    nowDate = datetime.now()
    lastDate = nowDate - timedelta(days=days)
    dicts = get_role(request)
    app = Application.objects.filter(apply_time__gt =lastDate)
    applys = {}
    while lastDate <= nowDate:
        applys[lastDate.strftime('%Y-%m-%d')] = 0
        lastDate += timedelta(days=1)
    for a in app:
        t = a.apply_time.strftime('%Y-%m-%d')
        if applys.has_key(t):
            applys[t] += 1
        else:
            applys[t] = 1
        
    dicts['days'] = days
    applys =  sorted(applys.iteritems(),key=lambda applys:applys[0],reverse=False)
    dicts['applys'] = simplejson.dumps(applys)
    return render_to_response(request, 'stats/apply.html', dicts)

@login_required
@is_alloter()
def task(request):
    days = request.GET.get('days', 90)
    days = int(days)
    if not days or days < 5:
        days = 30
    nowDate = datetime.now()
    lastDate = nowDate - timedelta(days=days)
    dicts = get_role(request)
    app = Application.objects.filter(apply_time__gt =lastDate)

    done = {}
    while lastDate <= nowDate:
        done[lastDate.strftime('%Y-%m-%d')] = 0
        lastDate += timedelta(days=1)
    for a in app:
        if a.finish_time:
            f = a.finish_time.strftime('%Y-%m-%d')
            if done.has_key(f):
                done[f] += 1
            else:
                done[f] = 1
    dicts['days'] = days
    done = sorted(done.iteritems(), key=lambda done:done[0], reverse=False)
    dicts['done'] = simplejson.dumps(done)

    return render_to_response(request,'stats/task.html', dicts)

@login_required
@is_alloter()
def evaluate(request):
    dicts = get_role(request)
    app = Application.objects.filter(evaluation__isnull = False)
    total = app.count()
    eva = {}
    eva_list = []
    for e in Application.evaluate_choices:
        eva_list.append([int(e[0]), e[1]])
        eva[int(e[0])] =  app.filter(evaluation = e[0]).count() * 1.0 / total * 100
    eva = sorted(eva.iteritems(), key=lambda eva:eva[0], reverse=True)
    dicts['evaluation'] = simplejson.dumps(eva)
    dicts['eva_list'] = simplejson.dumps(eva_list)
    return render_to_response(request, 'stats/evaluate.html', dicts)

@login_required
@is_alloter()
def atype(request):
    type_list = []
    count = []
    types = dict(ApplyType.type_choices)
    index = 0
    for t in types:
        type_list.append([index,types[t]])
        count.append([index,ApplyType.objects.filter(type = t).count()])
        index += 20
    dicts = get_role(request)
    dicts['count'] = simplejson.dumps(count)
   
    dicts['type_list'] = simplejson.dumps(type_list)

    return render_to_response(request,'stats/type.html', dicts)


@login_required
@is_staff()
def work(request):
    s_year  = request.GET.get('s_year', None)
    s_month = request.GET.get('s_month', None)
    s_day   = request.GET.get('s_day', None)
    e_year  = request.GET.get('e_year', None)
    e_month = request.GET.get('e_month', None)
    e_day   = request.GET.get('e_day', None)
    wtype   = request.GET.get('type', None)
    exp     = request.GET.get('export', None)

    today = date.today()

    try:
        s_year = int(s_year)
    except:
        s_year = None

    try:
        s_month = int(s_month)
    except:
        s_month = None

    try:
        s_day = int(s_day)
    except:
        s_day = None

    try:
        e_year = int(e_year)
    except:
        e_year = None

    try:
        e_month = int(e_month)
    except:
        e_month = None

    try:
        e_day = int(e_day)
    except:
        e_day = None

    if not e_year or not e_month:
        e_year = int(today.strftime('%Y'))
        e_month = int(today.strftime('%m'))

    if not e_day:
        tmp_date = date(e_year, e_month, 1) + relativedelta(months = 1) + relativedelta(days = -1)
        e_day = int(tmp_date.strftime('%d'))

    if not s_year or not s_month:
        s_year = e_year
        s_month = e_month

    if not s_day:
        s_day = 1

    if not wtype:
        wtype = 'task'

    start_time = date(s_year, s_month, s_day)
    end_time = date(e_year, e_month, e_day)
    husers = HelpDeskUser.objects.filter(role=HelpDeskUser.ROLE_OPERATOR)
    sobjs = {}
    for u in husers:
        if not sobjs.has_key(u.user.username):
            sobjs[u.user.username] = u.user
    # sobjs = User.objects.filter(username__in = staffs)
    dicts = get_role(request)
    tmp_time = start_time + relativedelta(months = -1)
    pre_s_year = tmp_time.strftime('%Y')
    pre_s_month = tmp_time.strftime('%m')
    pre_s_day = tmp_time.strftime('%d')
    tmp_time = start_time + relativedelta(months = 1)
    next_s_year = tmp_time.strftime('%Y')
    next_s_month = tmp_time.strftime('%m')
    next_s_day = tmp_time.strftime('%d')
    tmp_time = end_time + relativedelta(months = -1)
    pre_e_year = tmp_time.strftime('%Y')
    pre_e_month = tmp_time.strftime('%m')
    pre_e_day = tmp_time.strftime('%d')
    tmp_time = end_time + relativedelta(months = 1)
    next_e_year = tmp_time.strftime('%Y')
    next_e_month = tmp_time.strftime('%m')
    next_e_day = tmp_time.strftime('%d')
    dicts['pre_start_time'] = [pre_s_year, pre_s_month, pre_e_day]
    dicts['pre_end_time'] = [pre_e_year, pre_e_month, pre_e_day]
    dicts['next_start_time'] = [next_s_year, next_s_month, next_s_day]
    dicts['next_end_time'] = [next_e_year, next_e_month, next_e_day]
    dicts['start_time'] = [s_year, s_month, s_day]
    dicts['end_time'] = [e_year, e_month, e_day]
    dicts['type'] = wtype

    year_range=[]
    year_range_limit = 10
    tmp_year = int(today.strftime('%Y'))
    for i in range(0, year_range_limit):
        year_range.append(tmp_year)
        tmp_year -= 1
    month_range = [i for i in range(1,13)]
    dicts['year_range'] = year_range
    dicts['month_range'] = month_range

    if wtype == 'task':
        f = {}
        for staff,sobj in sobjs.items():
            tasks = Task.objects.filter(operator=staff, allot_time__gte=start_time, allot_time__lte=end_time, operate_time__isnull=False)
            u = []
            c = 0
            k = 0
            for task in tasks:
                task.response_time = (task.view_time - task.allot_time).seconds / 60.0
                task.handle_time = (task.operate_time - task.view_time).seconds / 60.0
                c += task.response_time
                k += task.handle_time
                u.append(task)

            f[staff] = {}
            f[staff]['list'] = u
            f[staff]['count'] = tasks.count()
            f[staff]['avg_resp'] = (f[staff]['count'] == 0 and [None] or [c / f[staff]['count']])[0]
            f[staff]['avg_hand'] = (f[staff]['count'] == 0 and [None] or [k / f[staff]['count']])[0]
            f[staff]['name'] = (sobj.first_name and [sobj.first_name] or [sobj.username])[0]    

        dicts['data'] = f  
        if exp == 'csv':        
            ## CSV      
            response = HttpResponse(mimetype='text/csv')  
            response['Content-Disposition'] = 'attachment; filename=%s（%d年%d月-%d年%d月）.csv' % ('任务', s_year, s_month, e_year, e_month)
            response.write('\xEF\xBB\xBF') 
            writer = csv.writer(response)  
            field_names = [ '姓名',
                            '数量',
                            '平均响应时间(分钟)',
                            '平均处理时间(分钟)',
                            '申请ID',
                            '处理时间(分钟)',
                            '分配人',
                            '分配时间',
                            '任务查看时间',
                            '任务完成时间',
                            '执行结果']
            writer.writerow(field_names)  
            

            for staff, obj in f.items():
                if obj['count'] == 0:
                    values = [obj['name'], obj['count']]
                    writer.writerow(values) 
                    continue
                first = True
                for o in obj['list']:
                    if first:
                        name = obj['name']
                        count = obj['count']
                        avg_resp = '%.1f'%obj['avg_resp']
                        avg_hand = '%.1f'%obj['avg_hand']
                        first = False
                    else:
                        name = ''
                        count = ''
                        avg_resp = ''
                        avg_hand = ''
                    values = [  name,
                                count,
                                avg_resp,
                                avg_hand,
                                o.uuid,
                                '%.1f'%o.handle_time,
                                o.alloter,
                                (o.allot_time + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S'),
                                (o.view_time + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S'),
                                (o.operate_time + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S'),
                                o.get_result()]
                    writer.writerow(values)   
            return response


        return render_to_response(request,'stats/work_task.html', dicts)
     