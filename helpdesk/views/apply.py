#coding=utf-8
import simplejson, uuid
from datetime import *
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseNotFound
from django.conf import settings

from utils import render_to_response, get_page, render_to_response_json
from utils.views import AbsView

from .. import get_role, send_mail, get_template, get_admin_email
from .. import APPLICATION_CATEGORIES, APPLICATION_CATEGORIES_LIST
from ..models import Application, HelpDeskUser, GeneralApplication,  ApplyType, Task

class ApplyView(AbsView):
    '''
        最基本的申请视图， 实现各个类型共用的功能， 提供跳转链接
    '''
    ApplicationModel = Application
    template_dir = 'apply/'

    form_field = [
        # ('field_name', True),   # field_name 必填字段
    ]  #申请表单字段

    urlmap = {
        r'^/$'          : ['index', ''],
        r'^/history$'   : ['history', ''],          # 用户申请记录列表
        r'^/query$'     : ['query', ''],            # 使用户历史申请查询
        r'^/allot$'     : ['allot_jump', ''],            # 管理员查看申请信息页面，跳转
        r'^/task$'      : ['task_jump', ''],             # 执行者查看申请信息页面，跳转
        r'^/ajax_type$' : ['ajax_type', ''],        # 标记申请分类标签
        r'^/evaluate$'  : ['evaluate', ''],         # 用户评价
        r'^/result$'    : ['result', 'apply_result'],
    }

    def index(self, request, template):
        return HttpResponseRedirect('/helpdesk/apply/query')

    def _get_role(self,request):
        dic = get_role(request)
        dic['apply_category'] = self.template_dir.strip('/')
        dic['apply_categories'] = APPLICATION_CATEGORIES_LIST
        return dic

    def _get_login_url(self, request):
        url = '/accounts/login?next=' + request.path
        args = []
        for key in request.GET.keys():
            args.append(key + '=' + request.GET[key])
        if args:
            url += '?' + '&'.join(args)
        return url

    def _get_uuid(self):
        return uuid.uuid4()

    def _get_template_dir(self, obj):
        return obj.category.split('Application')[0].lower() + '/'

        # if obj.category == 'GeneralApplication':
        #     return 'general/'
        # elif obj.category == 'VmApplication':
        #     return 'vm/'
        # else:
        #     return 'apply'

    def _get_form_param(self, request):
        data = {}
        error = {}
        for field, needed in self.form_field:
            data[field] = request.POST.get(field, None)
            if needed and data[field] == None:
                error[field] = '%s字段必填' % field
        if error == {}:
            return True, data
        return False, error

    def history(self, request, template):
        '''用户申请历史记录'''
        dicts = self._get_role(request)
        if not dicts.has_key('is_applicant'): 
            return HttpResponseRedirect(self._get_login_url(request))

        name    = request.GET.get('name')
        email   = request.GET.get('email')
        status  = request.GET.get('status')
        page    = request.GET.get('page')
        user    = HelpDeskUser.objects.filter(user = request.user, role='0')
        user    = user[0].user
        # dep     = [u.department for u in user]
        # apps    = self.ApplicationModel.objects.filter(department__in = dep).order_by('-apply_time')

        # only login user 
        apps = self.ApplicationModel.objects.filter(submit_user = user).order_by('-apply_time')

        if name:
            apps = apps.filter(name__contains = name)
        if email:
            apps = apps.filter(email__contains = email)
        if status:
            apps = apps.filter(status = status)

        p = get_page(apps, request)
        
        dicts['p'] = p
        dicts['statuslist'] = dict(self.ApplicationModel.status_choices)
        return render_to_response(request, get_template(template), dicts)

    def query(self, request, template):
        '''用户申请记录查询'''
        dicts = self._get_role(request)
        if not dicts.has_key('is_applicant'): 
            return HttpResponseRedirect(self._get_login_url(request))
            
        uuid = request.GET.get('uuid')
        if uuid:
            try:
                appobj = self.ApplicationModel.objects.get(pk=uuid)
                obj = False
                for application in dicts['apply_categories']:
                    if application['model'].__name__ == appobj.category:
                        obj = application['model'].objects.get(uuid = uuid)
                        dicts['application'] = appobj.category
                        dicts['apply_info_template'] = application['short_tag'] + '/info.html'
                        break
                
                for application in dicts['apply_categories']:
                    try:
                        obj = application['model'].objects.get(uuid = uuid)
                    except:
                        obj = None
                    if obj:
                        dicts['application'] = application['tag']
                        dicts['apply_info_template'] = application['short_tag'] + '/info.html'
                        appobj.category = application['tag']
                        appobj.save()
                        break
            except:
                obj = False

            dicts['uuid'] = uuid        
            if not obj:
                dicts['result'] = 'UUID 有误'
            else:
                dicts['app'] = obj
                dicts['task'] = appobj.task_set.filter()
        return render_to_response(request, get_template(template), dicts)

    def result(self, request, template):
        dicts = self._get_role(request)
        if not dicts.has_key('is_applicant'):
            return HttpResponseRedirect(self._get_login_url(request))

        uuid = request.GET.get('uuid')
        dicts['uuid'] = uuid
        return render_to_response(request, get_template(template), dicts)

    def  ajax_type(self, request, template):
        '''添加或删除申请类型标签'''
        dicts = self._get_role(request)
        if not dicts.has_key('is_alloter'): 
            return HttpResponseRedirect(self._get_login_url(request))

        if request.method == 'POST':
            uuid = request.POST.get('uuid')
            atype = request.POST.get('type')
            isadd = request.POST.get('isadd')
            if isadd == '1':
                try:
                    if not ApplyType.objects.filter(uuid=uuid, type=atype).exists():
                        a = ApplyType()
                        a.uuid_id = uuid
                        a.type = atype
                        a.save()
                except:
                    return render_to_response_json({'res':0})
            else:
                ApplyType.objects.filter(uuid=uuid, type=atype).delete()
            return render_to_response_json({'res':1})
        return HttpResponseNotFound()

    
    def allot_jump(self, request, template):
        '''各种类型申请审批页面的跳转连接'''
        dicts = self._get_role(request)
        if not dicts.has_key('is_alloter'): 
            return HttpResponseRedirect(self._get_login_url(request))

        uuid = request.GET.get('uuid')
        try:
            obj = self.ApplicationModel.objects.get(pk = uuid)
        except:
            return HttpResponseNotFound()
        tdir = self._get_template_dir(obj)
        return HttpResponseRedirect('/helpdesk/' + tdir + 'allot/view?uuid=' + uuid)
        
    def task_jump(self, request, template):
        '''任务详细信息页 跳转'''
        dicts = self._get_role(request)
        if not dicts.has_key('is_operator'): 
            return HttpResponseRedirect(self._get_login_url(request))

        id = request.GET.get('id')
        try:
            tobj = Task.objects.get(pk = id)
            obj = self.ApplicationModel.objects.get(pk = tobj.uuid_id)
        except:
            return HttpResponseNotFound()
        tdir = self._get_template_dir(obj)
        return HttpResponseRedirect('/helpdesk/'+ tdir +'task/view?id=' + id)


    def evaluate(self, request, template):
        try:
            if request.method == 'GET': 
                uuid = request.GET.get('uuid')
                score = request.GET.get('e')
                app = self.ApplicationModel.objects.get(uuid = uuid)   
                dicts = {}
                dicts['app'] = app
                dicts['e'] = score
                es = dict(self.ApplicationModel.evaluate_choices)
                dicts['ename'] =es[score]
                dicts['uuid'] = uuid
                score = int(score)
                if score < 60:
                    return render_to_response(request, 'evaluate.html', dicts)
                app.evaluation = str(score)
                app.evaluate_time = datetime.now()
                app.save()
            elif request.method == 'POST':
                uuid = request.POST.get('uuid')
                score = request.POST.get('e')
                app = self.ApplicationModel.objects.get(uuid = uuid) 
                content = request.POST.get('content')
                if content == '' or content == None:
                    return HttpResponse('提交失败')
                app.evaluate_content = content
                app.evaluation = str(score)
                app.evaluate_time = datetime.now()
                app.save()
            return HttpResponse('提交成功，谢谢。')
       
        except:
            return HttpResponse('提交失败，请稍后再试。。。')


    def _allot_handle(self, request, template):
        '''待分配申请列表 通用处理'''
        dicts = self._get_role(request)
        if not dicts.has_key('is_alloter'):
            return request, get_template(template), None

        apps        = self.ApplicationModel.objects.filter(status__in=('0', '5')).order_by('-apply_time')
        undocount   = apps.count()
        
        dicts['p']          = get_page(apps, request)
        dicts['undocount']  = undocount
        return request, get_template(template), dicts

    def _allot_list_handle(self, request, template):
        '''申请列表 通用处理'''
        dicts = self._get_role(request)
        if not dicts.has_key('is_alloter'):
            return request, get_template(template), None

        name    = request.GET.get('name')
        email   = request.GET.get('email')
        status  = request.GET.get('status')
        page    = request.GET.get('page')

        apps    = self.ApplicationModel.objects.all().order_by('-apply_time')
        if name:
            apps = apps.filter(name__contains = name)
        if email:
            apps = apps.filter(email__contains = email)
        if status:
            apps = apps.filter(status = status)

        p = get_page(apps, request)
        dicts['p'] = p
        dicts['statuslist'] = dict(self.ApplicationModel.status_choices)
        return request, get_template(template), dicts

    def _allot_view_handle(self, request, template):
        '''审批页面 通用处理'''
        dicts = self._get_role(request)
        if not dicts.has_key('is_alloter'):
            return request, get_template(template), None

        uuid = request.GET.get('uuid')
        try:
            app = self.ApplicationModel.objects.get(uuid=uuid)
        except:
            return HttpResponseNotFound()

        app.set_view_time_if_first(request)
        
        ud = HelpDeskUser.objects.all()
        user_duty = {}
        for u in ud:
            if not user_duty.has_key(u.duty):
                user_duty[u.duty] = []
            user_duty[u.duty].append((u.duty, u.user.username, u.user.first_name))

        dicts['app']        = app
        dicts['duty']       = dict(HelpDeskUser.duty_choices)
        dicts['user_duty']  = simplejson.dumps(user_duty)
        dicts['al']         = app.task_set.filter()
        dicts['types']      = dict(ApplyType.type_choices)
        dicts['type']       = ApplyType.objects.filter(uuid=uuid)


        dicts['apply_info_template'] = '%s/info.html' % dicts['apply_category']

        return request, get_template(template), dicts

    def _task_handle(self, request, template):
        '''待处理任务列表 通用处理'''
        dicts = self._get_role(request)
        if not dicts.has_key('is_operator'):
            return request, get_template(template), None

        al = Task.objects.filter(operator = request.user, result='0', uuid__category=self.ApplicationModel.__name__)
        dicts['p'] = get_page(al, request)
        return request, get_template(template), dicts
        
    def _task_list_handle(self, request, template):
        '''所有任务列表 通用处理'''
        dicts = self._get_role(request)
        if not dicts.has_key('is_operator'):
            return request, get_template(template), None

        name    = request.GET.get('name')
        email   = request.GET.get('email')
        duty    = request.GET.get('duty')
        result  = request.GET.get('result')

        als = Task.objects.filter(operator = request.user, uuid__category=self.ApplicationModel.__name__)
      
        if name:
            als = als.filter(uuid__name__contains = name)
        if email:
            als = als.filter(uuid__email__contains = email)
        if duty:
            als = als.filter(operator_duty = duty)
        if result:
            als = als.filter(result = result)

        als = als.order_by('-allot_time')
        dicts['p'] = get_page(als, request )
        dicts['result_list'] = dict(Task.result_choices)
        dicts['duty_list'] = dict(HelpDeskUser.duty_choices)
        return request, get_template(template), dicts
        
    def _task_view_handle(self, request, template):
        '''任务详细信息页 通用处理'''
        dicts = self._get_role(request)
        if not dicts.has_key('is_operator'):
            return request, get_template(template), None

        id = request.GET.get('id')
        try:
            al = Task.objects.get(pk=id, operator = request.user)
        except:
            return request, get_template(template), None

        al.set_view_time_if_first()
        print al.uuid
        print self.ApplicationModel.objects.all()
        app = self.ApplicationModel.objects.get(uuid = al.uuid_id)
        als = Task.objects.filter(uuid = al.uuid_id).order_by('-allot_time')

        dicts['app']     = app
        dicts['als']     = als
        dicts['al']      = al
        # dicts['types'] = dict(ApplyType.type_choices)
        dicts['type']    = ApplyType.objects.filter(uuid=al.uuid_id)
        dicts['results'] = dict(Task.result_choices)
        del(dicts['results']['0'])
        return request, get_template(template), dicts


##################################################################################
############################  以下方法用于继承或需要重写  ########################
##################################################################################

    def allot(self, request, template):
        '''待分配申请列表'''
        request, template, dicts = self._allot_handle(request, template)
        if dicts == None:
            return HttpResponseRedirect(self._get_login_url(request))
        return render_to_response(request, template, dicts)

    def allot_list(self, request, template):
        '''所有申请列表'''
        request, template, dicts = self._allot_list_handle(request, template)
        if dicts == None:
            return HttpResponseRedirect(self._get_login_url(request))
        return render_to_response(request, template, dicts)

    def allot_view(self, request, template):
        '''审批页面'''
        request, template, dicts = self._allot_view_handle(request, template)
        if dicts == None:
            return HttpResponseRedirect(self._get_login_url(request))
        return render_to_response(request, template, dicts)

    def task(self, request, template):
        '''待处理任务列表'''
        request, template, dicts = self._task_handle(request, template)
        if dicts == None:
            return HttpResponseRedirect(self._get_login_url(request))
        return render_to_response(request, template, dicts)

    def task_list(self, request, template):
        '''任务列表'''
        request, template, dicts = self._task_list_handle(request, template)
        if dicts == None:
            return HttpResponseRedirect(self._get_login_url(request))
        return render_to_response(request, template, dicts)

    def task_view(self, request, template):
        '''任务详细信息页'''
        request, template, dicts = self._task_view_handle(request, template)
        if dicts == None:
            return HttpResponseRedirect(self._get_login_url(request))
        return render_to_response(request, template, dicts)
        

    def ajax_del_op(self, request, template):
        '''在任务分配界面 删除任务'''
        dicts = self._get_role(request)
        if not dicts.has_key('is_alloter'):
            return HttpResponseRedirect(self._get_login_url(request))

        if request.method == 'POST':
            uuid = request.POST.get('uuid')
            id   = request.POST.get('id')
            try:
                Task.objects.filter(uuid=uuid, pk=id).delete()
                obj = self.ApplicationModel.objects.get(uuid=uuid)
                if obj.update_status(request):
                    #给申请人发送通知邮件
                    obj.evaluatelink = '/helpdesk/apply/evaluate?uuid=' + str(obj.uuid) + '&e='
                    obj.link = '/helpdesk/apply/query?uuid=' + str(obj.uuid)
                    obj.evaluatelist = obj.evaluate_choices
                    tdir = self._get_template_dir(obj)
                    send_mail(request, obj, tdir + 'mail_user_status.html', [obj.email])
            except:
                return render_to_response_json({'res':0})
            return render_to_response_json({'res':1})
        return HttpResponseNotFound()


    def _do_allot(self, request, o):
        return True

    def ajax_allot(self, request, template):
        dicts = self._get_role(request)
        if not dicts.has_key('is_alloter'):
            return HttpResponseRedirect(self._get_login_url(request))

        if request.method == 'POST':
            uuid = request.POST.get('uuid')
            operator = request.POST.getlist('operator[]')
            try:
                app = self.ApplicationModel.objects.get(uuid = uuid)
            except:
                return render_to_response_json({'res':0})
            res = False
            for o in operator:
                o = o.split(',')
                res = app.allot(request, request.user, o[0], o[1])
                if res:
                    #给执行人发送通知邮件
                    app.link = '/helpdesk/apply/task?id=' + str(res.pk)
                    app.taskobj = res
                    op = HelpDeskUser.objects.filter(user__username=o[1], duty=o[0])
                    if op.exists():
                        send_mail(request, app, get_template('%smail_op_task.html'%self.template_dir), [op[0].email], u'HelpDesk通知 【' + app.name +'】')
            if res:
                self._do_allot(request, app)
                app.update_status(request, '2')
                #给申请人发送通知邮件
                app.evaluatelink = '/helpdesk/apply/evaluate?uuid=' + str(app.uuid) + '&e='
                app.link = '/helpdesk/apply/query?uuid=' + str(app.uuid)
                app.evaluatelist = app.evaluate_choices
                send_mail(request, app, get_template('%smail_user_status.html'%self.template_dir), [app.email])
                
            return render_to_response_json({'res':1})
        return HttpResponseNotFound()


    def _do_reject(self, request, o):
        return True

    def ajax_reject(self, request, template):
        dicts = self._get_role(request)
        if not dicts.has_key('is_alloter'):
            return HttpResponseRedirect(self._get_login_url(request))

        if request.method == 'POST':
            uuid = request.POST.get('uuid')
            content = request.POST.get('content')
            ok = True
            try:
                app = self.ApplicationModel.objects.get(uuid=uuid)
            except:
                ok = False

            if not app.reject(request, request.user, content):
                ok = False
            else:
                self._do_reject(request, app)

            if ok:
                #给申请人发送通知邮件
                app.evaluatelink = '/helpdesk/apply/evaluate?uuid=' + str(app.uuid) + '&e='
                app.link         = '/helpdesk/apply/query?uuid=' + str(app.uuid)
                app.evaluatelist = app.evaluate_choices
                send_mail(request, app, get_template('%smail_user_status.html'%self.template_dir), [app.email])
                return render_to_response_json({'res':1})
            else:
                return render_to_response_json({'res':0})

        return HttpResponseNotFound()

    def _do_result(self, request, o):
        '''任务处理结果  附加处理  在子类中根据需要重写此方法'''
        return True

    def ajax_result(self, request, template):
        '''任务处理结果'''
        dicts = self._get_role(request)
        if not dicts.has_key('is_operator'):
            return HttpResponseRedirect(self._get_login_url(request))

        if request.method == 'POST':
            id      = request.POST.get('id')
            result  = request.POST.get('result')
            remarks = request.POST.get('remarks')

            app = None
            try:
                al = Task.objects.get(pk = id, operator = request.user)
            except:
                return render_to_response_json({'res':0})

            al.result = result
            al.operate_remark = remarks
            al.operate_time = datetime.now()
            
            app = self.ApplicationModel.objects.get(pk=al.uuid_id)
            app.taskobj = al

            if  self._do_result(request, app):
                al.save()

                if app.update_status(request):
                    #给申请人发送通知邮件
                    app.evaluatelink = '/helpdesk/apply/evaluate?uuid=' + str(app.uuid) + '&e='
                    app.link = '/helpdesk/apply/query?uuid=' + str(app.uuid)
                    app.evaluatelist = app.evaluate_choices
                    send_mail(request, app, get_template('%smail_user_status.html'%self.template_dir), [app.email])
                    
                return render_to_response_json({'res':1})
            return render_to_response_json({'res':0})
        return HttpResponseNotFound()



