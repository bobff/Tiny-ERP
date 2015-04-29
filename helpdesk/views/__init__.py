#coding=utf-8
from django.http import HttpResponseRedirect, HttpResponseNotFound, HttpResponse
from django.contrib.auth.decorators import login_required

from utils import render_to_response_json, dispatch_url, render_to_response

from ..models import HelpDeskUser, Application, Task
from .. import is_alloter, is_applicant, is_operator, APPLICATION_CATEGORIES, APPLICATION_CATEGORIES_LIST, get_role

from .apply import ApplyView


def root(request, url):
    urlmap = {
        r'^apply':ApplyView,
    }
    from .. import APPLICATION_VIEWS
    for k, v in APPLICATION_VIEWS.items():
        urlmap[r'^%s' % k] = v

    return dispatch_url(urlmap, url, request)

@login_required
def index(request):
    role = HelpDeskUser.objects.filter(user = request.user)
    if role:
        role = role[0]
        if role.role == '0':
            return HttpResponseRedirect('/helpdesk/general/apply')
        elif role.role == '1':
            return HttpResponseRedirect('/helpdesk/general/allot')
        elif role.role == '2':
            return HttpResponseRedirect('/helpdesk/general/task')
    if request.user.is_staff:
        return HttpResponseRedirect('/helpdesk/search')
    return HttpResponseRedirect('/accounts/login/?next=/helpdesk/')

@login_required
def passwd(request):
    dicts = get_role(request)
    if request.method == 'POST':
        old_passwd = request.POST.get('old_passwd')
        passwd = request.POST.get('passwd')
        passwd_check = request.POST.get('passwd_check')
        if not old_passwd or not passwd or not passwd_check:
            dicts['msg'] = '请完整填写表单！'
        elif not request.user.check_password(old_passwd):
            dicts['msg'] = '当前密码错误！'
        elif passwd != passwd_check:
            dicts['msg'] = '两次输入的新密码不一致！'
        else:
            try:
                request.user.set_password(passwd)
                request.user.save()
                dicts['msg'] = "密码修改成功！"
            except:
                dicts['msg'] = "密码修改失败！"
    return render_to_response(request, 'passwd.html', dicts)



def get_unallot(request):
    apply_categories = APPLICATION_CATEGORIES
    #from helpdesk.models import GeneralApplication, VmApplication, VpnApplication
    unallots = Application.objects.filter(status__in=('0','5'))
    uuids = [a.uuid + "/" + a.status for a in unallots]
    count = unallots.count()
    dicts = {'count':count, 'uuids':uuids}
    for k, v in apply_categories.items():
        try:
            dicts[k] = v['model'].objects.filter(status__in=('0', '5')).count()
        except:
            dicts[k] = 0
    return dicts

@is_alloter()
def ajax_get_unallot(request):
    if request.method == 'POST':
        dicts = get_unallot(request)
        return render_to_response_json(dicts)
    return HttpResponseNotFound()

def get_undo(request):
    apply_categories = APPLICATION_CATEGORIES
    undos = Task.objects.filter(operator = request.user, result='0')
    uuids = [a.pk for a in undos]
    count = undos.count()
    dicts = {'count':count, 'uuids':uuids}
    for k, v in apply_categories.items():
        try:
            dicts[k] = Task.objects.filter(operator = request.user, result='0', uuid__category=v['tag']).count()
        except:
            dicts[k] = 0
    return dicts

@is_operator()
def ajax_get_undo(request):
    if request.method == 'POST':
        dicts = get_undo(request)
        # general = Task.objects.filter(operator = request.user, result='0', uuid__category='GeneralApplication').count()
        # vm = Task.objects.filter(operator = request.user, result = '0', uuid__category = 'VmApplication').count()
        # vpn = Task.objects.filter(operator = request.user, result = '0', uuid__category = 'VpnApplication').count()
        return render_to_response_json(dicts)
    return HttpResponseNotFound()



@is_alloter()
def allot_jump(request):
    dicts = get_unallot(request)
    for c in APPLICATION_CATEGORIES_LIST:
        if dicts[c['short_tag']] > 0:
            return HttpResponseRedirect('/helpdesk/%s/allot' % c['short_tag'])
    return HttpResponseRedirect('/helpdesk/general/allot')

@is_operator()
def operate_jump(request):
    dicts = get_undo(request)
    for c in APPLICATION_CATEGORIES_LIST:
        if dicts[c['short_tag']] > 0:
            return HttpResponseRedirect('/helpdesk/%s/task' % c['short_tag'])
    return HttpResponseRedirect('/helpdesk/general/task')


