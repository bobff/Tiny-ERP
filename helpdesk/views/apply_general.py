#coding=utf-8
import simplejson, uuid
from datetime import *
from django.http import HttpResponseRedirect, HttpResponse


from utils import render_to_response, get_page, render_to_response_json
from utils.views import AbsView

from helpdesk import get_role, send_mail, get_template, get_admin_email
from helpdesk.models import Application, HelpDeskUser, GeneralApplication,  ApplyType, Task, Package
from helpdesk.views.apply import ApplyView

class GeneralApplyView(ApplyView):
    ApplicationModel = GeneralApplication
    template_dir = ApplicationModel.__name__.split('Application')[0].lower() + '/'

    urlmap = {
        r'^/$'              : ['index', ''],
        r'^/apply$'         : ['apply', ''],
        r'^/append$'        : ['append', ''],
        

        r'^/allot$'         : ['allot', 'allot'],
        r'^/allot/list$'    : ['allot_list', ''],
        r'^/allot/view$'    : ['allot_view', ''],

        
        r'^/ajax_allot$'    : ['ajax_allot', ''],
        r'^/ajax_reject$'   : ['ajax_reject', ''],
        r'^/ajax_del_op$'   : ['ajax_del_op', ''],
        
        r'^/task$'          : ['task', ''],
        r'^/task/list$'     : ['task_list', ''],
        r'^/task/view$'     : ['task_view', ''],

        r'^/ajax_result$'   : ['ajax_result', ''],
    }

    def apply(self, request, template):
        dicts = self._get_role(request)
        if not dicts.has_key('is_applicant'):
            return HttpResponseRedirect(self._get_login_url(request))

        if request.method == 'POST':
            name        = request.POST.get('name').strip()
            email       = request.POST.get('email').strip()
            content     = request.POST.get('content').strip()
            department  = HelpDeskUser.objects.filter(user = request.user, role='0')
            
            verified = True
            if not department:
                verified = False
            if name == None or name == '' or len(name) > 100:
                verified = False
            if email == None or email == '' or len(email) > 100:
                verified = False
            if content == '' or content == None:
                verified = False

            if verified == False:
                dicts = dicts.update({'name':name, 'email':email, 'content':content, 'verifyinfo':'请正确填写表单'})
                return render_to_response(request, template,dicts)

            department  = department[0]
            app         = self.ApplicationModel()
            app.uuid    = self._get_uuid()
            app.name    = name
            app.department = department.department
            app.email   = email
            app.submit_user = request.user
            app.content = content
            app.status  = 0
            if request.META.has_key('HTTP_X_FORWARDED_FOR'):
                app.ip = request.META['HTTP_X_FORWARDED_FOR']
            else:
                app.ip = request.META['REMOTE_ADDR']
            app.save()

             
            # 给管理员发通知邮件
            app.link = '/helpdesk/apply/allot?uuid=' + str(app.uuid)
            alloters = HelpDeskUser.objects.filter(role = '1')
            receiver = get_admin_email()
            send_mail(request,app, get_template('%smail_adm_apply.html' % self.template_dir), receiver, u'HelpDesk通知 【' + app.name +'】')
            
            # 给用户发通知邮件
            app.link = '/helpdesk/apply/query?uuid=' + str(app.uuid)
            send_mail(request,app, get_template('%smail_user_new.html'%self.template_dir), [app.email])
            
            return HttpResponseRedirect('/helpdesk/apply/result?uuid=' + str(app.uuid))

        return render_to_response(request,template,dicts)

    def append(self, request, template):
        dicts = self._get_role(request)
        if not dicts.has_key('is_applicant'):
            return HttpResponseRedirect(self._get_login_url(request))

        if request.method == 'POST':
            application = request.POST.get('application')
            name        = request.POST.get('name')
            content     = request.POST.get('content')
            app         = self.ApplicationModel.objects.get(pk = application)
            app.append(request, {'name':name,'content':content})

        # 给申请者发送邮件
        app.link = '/helpdesk/apply/query?uuid=' + str(app.uuid)
        send_mail(request,app, get_template('%smail_user_append.html' % self.template_dir), [app.email])

        # 给管理员发送有邮件
        alloters = HelpDeskUser.objects.filter(role = '1')
        receiver = get_admin_email()
        app.link = '/helpdesk/apply/allot?uuid=' + str(app.uuid)
        send_mail(request,app, get_template('%smail_adm_apply.html'%self.template_dir), receiver, u'HelpDesk通知 【' + app.name +'】')
       
        return HttpResponseRedirect('/helpdesk/apply/query?uuid=' + application)




    def _do_allot(self, request, o):
        for p in o.package_set.all():
            p.viewed = True
            p.save()
        return True

    def _do_result(self, request, o):
        for p in  Package.objects.filter(application = o.pk):
            p.viewed = True
            p.save()
            
        return True


