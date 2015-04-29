#coding=utf-8
from django.shortcuts import render
from django.contrib.auth.decorators import login_required 
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

from utils import render_to_response, render_to_response_json

from ..models import  Schedule
from django.utils.timezone import localtime, make_aware, get_current_timezone

from .. import get_role
import time

@login_required
def scheduling(request):
    dicts = get_role(request)
    return render_to_response(request, 'calendar.html', dicts)

@login_required
def add(request):
    id = request.POST.get('id', None)
    start_time = request.POST.get('start_date', None)
    end_time = request.POST.get('end_date', None)
    remarks = request.POST.get('remarks')
    public = request.POST.get('public')
    if not public:
        public = False
    else:
        public = True

    if not id or not start_time or not end_time:
        return render_to_response_json({'res':False})

    ap = Schedule()
    ap.id = id
    ap.user = request.user
    ap.start_time = make_aware(datetime.strptime(start_time,'%Y-%m-%d %H:%M:%S'), get_current_timezone())
    ap.end_time = make_aware(datetime.strptime(end_time,'%Y-%m-%d %H:%M:%S'), get_current_timezone())
    ap.remarks = remarks
    ap.public = public
    try:
        ap.save()
    except:
        return render_to_response_json({'res':False, 'msg': '保存失败'})
    return render_to_response_json({'res':True})

@login_required
def update(request):
    id = request.POST.get('id', None)
    start_time = request.POST.get('start_date', None)
    end_time = request.POST.get('end_date', None)
    remarks = request.POST.get('remarks')
    public = request.POST.get('public')

    if public == 'false':
        public = False
    else:
        public = True

    if not id or not start_time or not end_time:
        return render_to_response_json({'res':False})

    try:
        obj = Schedule.objects.get(pk=id)
    except:
        return render_to_response_json({'res':False, 'msg':'参数有误'})

    if obj.user != request.user:
        data = {'res':False, 'msg': '您没有权限修改该记录'}
        return render_to_response_json(data)

    obj.start_time = make_aware(datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S'), get_current_timezone())
    obj.end_time = make_aware(datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S'), get_current_timezone())
    obj.remarks = remarks
    obj.public = public
    try:
        obj.save()
    except:
        return render_to_response_json({'res':False, 'msg': '保存失败'})    
    return render_to_response_json({'res':True})

@login_required
def delete(request):
    id = request.POST.get('id')
    obj = Schedule.objects.filter(pk=id)
    if not id or not obj:
        return render_to_response_json({'res':-1})

    obj = obj[0]
    if obj.user != request.user:
        return render_to_response_json({'res':False, 'msg':'您没有权限删除该记录'})

    try:
        obj.delete()
        return render_to_response_json({'res':True, 'msg':'删除成功'})
    except:
        return render_to_response_json({'res':False, 'msg':'删除失败'}) 

@login_required
def load(request):
    mode = request.GET.get('mode')
    t = request.GET.get('t')
    try:
        t = long(t) / 1000
    except:
        t = None

    if mode == 'day':
        if t:
            start_time = datetime.fromtimestamp(t)
        else:
            now = datetime.now()
            start_time = datetime(now.year, now.month, now.day, 0, 0)
        end_time = start_time + relativedelta(days=1)
    elif mode == 'week':
        if t:
            start_time = datetime.fromtimestamp(t)
        else:
            now = datetime.now()
            start_time = datetime(now.year, now.month, now.day, 0, 0) + relativedelta(days=(-1*now.weekday()))
        end_time = start_time + relativedelta(weeks=1)
    elif mode == 'month':
        if t:
            start_time = datetime.fromtimestamp(t)
        else:
            now = datetime.now()
            start_time = datetime(now.year, now.month, 1, 0, 0)
        end_time = start_time + relativedelta(months=1)
    elif mode == 'timeline':
        if t:
            start_time = datetime.fromtimestamp(t)
        else:
            now = datetime.now()
            start_time = datetime(now.year, now.month, now.day, 0, 0) + relativedelta(days=(-1*now.weekday()))
        end_time = start_time + relativedelta(weeks=1)
    else:
        return render_to_response_json([])

    objs = Schedule.objects.filter(user=request.user, public=False, start_time__lte = end_time, end_time__gt = start_time)

    ev = []
    for obj in objs:
        ev.append({
            'id':obj.id, 
            'text':obj.remarks,
            'start_date': localtime(obj.start_time).strftime('%m/%d/%Y %H:%M'),
            'end_date': localtime(obj.end_time).strftime('%m/%d/%Y %H:%M'),
            'public': obj.public,
            'section_id': 1
            })
    public_objs = Schedule.objects.filter(public=True,start_time__lte = end_time, end_time__gt = start_time)
    for obj in public_objs:
        ev.append({
            'id':obj.id, 
            'text':((request.user != obj.user) and "【公共日程】" or "") + obj.remarks + ((request.user != obj.user) and (" (%s)" % obj.user)  or ""),
            'start_date': localtime(obj.start_time).strftime('%m/%d/%Y %H:%M'),
            'end_date': localtime(obj.end_time).strftime('%m/%d/%Y %H:%M'),
            'public': obj.public,
            'section_id': 1,
            'readonly':(request.user != obj.user),
            'color': '#808080'
            })

    return render_to_response_json(ev)