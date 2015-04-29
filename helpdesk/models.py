# coding: utf-8#
import sys;reload(sys);sys.setdefaultencoding('utf8') #设置全局字符集
from datetime import *
from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings  
from dicts.models import Department

class HelpDeskUser(models.Model):
    '''
        HelpDesk用户, 主要用于用户角色划分
    '''
    duty_choices=(
        ('0','网管'),
        ('1','系统'),
        ('2','存储'),
        ('3','服务台'),
    )
    ROLE_USER = '0'
    ROLE_ADMIN = '1'
    ROLE_OPERATOR = '2'
    role_choices=(
        (ROLE_USER,'普通用户'),
        (ROLE_ADMIN,'管理员'),
        (ROLE_OPERATOR,'操作员'),
        
    )#前面是在数据库中保存的值，后面是页面上展示的形式
    user    = models.ForeignKey(User, verbose_name='用户')
    department = models.ForeignKey(Department, verbose_name='部门')
    role    = models.CharField('角色',max_length=10,choices=role_choices)
    duty    = models.CharField('操作员职责', max_length=10, choices=duty_choices, null=True,blank=True)
    email   = models.CharField('邮箱', max_length=100)
    phone   = models.CharField('座机号', max_length=100,null=True,blank=True)
    mobile  = models.CharField('手机号', max_length=100,null=True,blank=True)    
    address = models.CharField('办公地址', max_length=100,null=True,blank=True)

    class Meta:
        #db_table = 'info'
        verbose_name = 'HelpDesk用户'
        verbose_name_plural = 'HelpDesk用户'
    
    def __unicode__(self):
        return self.user.username



class Application(models.Model):
    '''
    申请操作记录表， 所有类型申请的申请操作，
        生成UUID、记录申请人信息、申请时间、查看时间、处理时间、完成时间、用户评价等通用信息
    '''
    status_choices=(
        ('0', '审核中'),
        ('1', '驳回'),
        ('2', '处理中'),
        ('3', '完成'),
        ('4', '无法处理'),
        ('5', '附加申请'),
    )

    evaluate_choices = (
        ('100', '十分满意'),
        ('75',  '满意'),
        ('50',  '一般'),
        ('25',  '不满意'),
        ('0',   '十分不满意'),
    )

    uuid        = models.CharField(max_length=50, primary_key=True)
    name        = models.CharField('姓名', max_length=100)
    department  = models.ForeignKey(Department, verbose_name='部门')
    email       = models.CharField('Email', max_length=100)
    ip          = models.IPAddressField('申请者IP地址')
    status      = models.CharField('状态', max_length=100, choices=status_choices)
    status_remark = models.TextField('状态说明', null=True, blank=True)
    evaluation  = models.CharField('评价', max_length=50, choices=evaluate_choices, null=True, blank=True)
    evaluate_content = models.TextField('用户意见', null=True, blank=True)
    apply_time  = models.DateTimeField('申请时间', auto_now_add=True)
    viewer      = models.CharField('首次查看者', max_length=100, null=True, blank=True)
    view_time   = models.DateTimeField('首次查看时间', null=True, blank=True)
    finish_time = models.DateTimeField('结束时间', null=True, blank=True)
    evaluate_time = models.DateTimeField('评价时间', null=True, blank=True)
    category    = models.CharField('类别', max_length=100)

    submit_user    = models.ForeignKey(User, verbose_name='提交用户', null=True)

    class Meta:
        verbose_name = '申请'
        verbose_name_plural = '申请'

    def get_status(self):
        dic = dict(self.status_choices)
        if dic.has_key(self.status):
            return dict(self.status_choices)[self.status]
        return ''

    def get_evaluation(self):
        if self.evaluation == None or self.evaluation == '':
            return '--'
        return dict(self.evaluate_choices)[self.evaluation]

    def get_department(self):
        return self.department.name

    def get_category(self):
        from . import APPLICATION_CATEGORIES
        for category in APPLICATION_CATEGORIES.values():
            if category['tag'] == self.category:
                return category['name']
        return '其他'

    def get_short_category(self):
        from . import APPLICATION_CATEGORIES
        for short, category in APPLICATION_CATEGORIES.items():
            if category['tag'] == self.category:
                return short
        return ''
        
    def set_view_time_if_first(self, request):
        if self.viewer == None or self.viewer == '' or self.view_time == None or self.view_time == '':
            self.view_time = datetime.now()
            self.viewer = str(request.user)
            self.save()

    def update_status(self, request, s = None):
        '''
            application
            status_choices=(
                ('0', '审核中'),
                ('1', '驳回'),
                ('2', '处理中'),
                ('3', '完成'),
                ('4', '无法处理'),
                ('5', '附加申请'),
            )
            task
            result_choices = (
                ('0', '待处理'),
                ('1', '无法处理'),
                ('2', '完成'),
            )
        '''
        if s == None:
            if self.status in ('0', '1'):  #如果处于审核中或驳回状态，不查询task
                return True
            status = '3'   #默认设置为 完成
            no_task = True
            for a in self.task_set.all():
                no_task = False
                if a.result == '1':  #如果任务无法处理，则申请无法处理
                    status = '4'
                    break
                elif a.result != '2': #如果有没有完成并且不是无法处理的任务，则申请状态为处理中
                    status = '2'
            if no_task:   #一个任务都没有  则设置为 处理中
                status = '2'
            
        else:
            status = s

        if status != self.status:
            self.status = status            
            if status in ('3', '4'): #完成或无法处理
                self.finish_time = datetime.now()
                self.evaluation = '100'
            elif status == '1': #驳回
                self.finish_time = datetime.now()
            else:
                self.finish_time = None
            self.save()

            return True
        return False



    def allot(self, request, alloter, duty, operator):
        al = Task.objects.filter(uuid=self.uuid, operator=operator, operator_duty=duty)

        if not al:
            al = Task()
            al.uuid_id = self.uuid
            al.alloter = alloter
            al.operator_duty = duty
            al.operator = operator
            #al.package_id = package

            try:
                al.save()
            except:
                return False
        else:
            al = al[0]
            al.result = '0'
            al.save()
            print 3, al.result

       
        return al
    
    def reject(self, request, alloter, content):
        try:        
            self.alloter = alloter
            self.status_remark = content
            self.update_status(request,'1')
            self.save()
            self.task_set.all().delete()
        except:
            return False
        return True

    def save(self):
        if self.__class__.__name__ != 'Application':
            self.category = self.__class__.__name__
        return super(Application, self).save()


class GeneralApplication(Application):
    content = models.TextField('正文')

    class Meta:
        verbose_name = '综合申请'
        verbose_name_plural = verbose_name

    # def save(self):
    #     self.category = 'GeneralApplication'
    #     return super(GeneralApplication, self).save()


    def append(self, request, dicts): #条件附加申请 dicts = {'name':xxx, 'content:xxxx}
        if not dicts.has_key('name') or not dicts.has_key('content'):
            return False
        if request.META.has_key('HTTP_X_FORWARDED_FOR'):
            ip = request.META['HTTP_X_FORWARDED_FOR']
        else:
            ip = request.META['REMOTE_ADDR']
        
        package = Package()
        package.application = self
        package.name = dicts['name']
        package.content = dicts['content']
        package.ip = ip
        # package.status = '0'
        try:
            package.save()
        except:
            return False
        self.status = '5'
        self.save()

        return True
        
    def update_status(self, request, s=None):
        res = super(GeneralApplication,self).update_status(request,s)
        if res:
            for p in self.package_set.all():  #如果有没有处理的附加申请  则状态改为附加申请
                if p.viewed == False:
                    self.status = '5'
                    self.save()
                    break

        return res

    def __unicode__(self):
        return self.uuid 


class Package(models.Model):
    application = models.ForeignKey(GeneralApplication)
    name        = models.CharField('姓名', max_length=100)
    ip          = models.IPAddressField('申请者IP地址')
    content     = models.TextField('正文')
    # status = models.CharField('状态', max_length=100, choices=status_choices)
    # status_remark = models.TextField('状态说明', null=True, blank=True)
    apply_time  = models.DateTimeField('申请时间', auto_now_add=True)
    viewer      = models.CharField('首次查看者', max_length=100, null=True, blank=True)
    view_time   = models.DateTimeField('首次查看时间', null=True, blank=True)
    finish_time = models.DateTimeField('结束时间', null=True, blank=True)
    viewed      = models.BooleanField('是否已查看', default=False)

class Task(models.Model):
    result_choices = (
        ('0', '待处理'),
        ('1', '无法处理'),
        ('2', '完成'),
    )

    uuid            = models.ForeignKey(Application)
    #uuid    = models.CharField(max_length=50, primary_key=True)
    #package = models.ForeignKey(Package, null=True,blank=True)
    alloter         = models.CharField('分配人', max_length=100)
    allot_time      = models.DateTimeField('分配时间', auto_now_add=True)
    allot_remark    = models.TextField('分配备注', null=True, blank=True)
    operator        = models.CharField('执行人', max_length=100)
    operator_duty   = models.CharField('执行人职责', max_length=100, choices = HelpDeskUser.duty_choices)
    view_time       = models.DateTimeField('任务查看时间', null=True, blank=True)
    operate_time    = models.DateTimeField('任务完成时间', null=True, blank=True)
    operate_remark  = models.TextField('执行备注', null=True, blank=True)
    result          = models.CharField('执行结果', max_length=10, choices = result_choices, default='0')
        
    class Meta:
        verbose_name = '任务'
        verbose_name_plural = '任务'


    def get_operator_duty(self):
        return dict(HelpDeskUser.duty_choices)[self.operator_duty]

    def get_operator(self):
        return self._get_helpdeskuser(self.operator, self.operator_duty)
    operator_data = property(get_operator)
    def get_alloter(self):
        return self._get_helpdeskuser(self.alloter)
    alloter_data = property(get_alloter)

    def _get_helpdeskuser(self, user, duty=None):
        try:
            u = HelpDeskUser.objects.filter(user__username = user)
            if duty:
                u = u.filter(duty = duty)
        except:
            return None
        if u.exists():
            return u[0]
        return None

    def get_result(self):
        if self.result:
            return dict(self.result_choices)[self.result]
        return None
    
    def set_view_time_if_first(self):
        if self.view_time == None or self.view_time == '':
            self.view_time = datetime.now()
            self.save()

class ApplyType(models.Model):
    type_choices = (
        ('0', '申请'),
        ('1', '故障'),
        ('2', '业务'),
        ('3', '提问'),
        ('99', '其它'),
    )
    uuid = models.ForeignKey( Application)
    type = models.CharField('类型', max_length=10, choices=type_choices)

    def get_type(self):
        return dict(self.type_choices)[self.type]

    class Meta:
        verbose_name = '申请类型'
        verbose_name_plural = '申请类型'


class Schedule(models.Model):
    id = models.CharField('ID', max_length=100, primary_key=True)
    user = models.ForeignKey(User, verbose_name='用户')
    start_time = models.DateTimeField('开始时间')
    end_time = models.DateTimeField('结束时间')
    remarks = models.TextField('内容')
    remind = models.IntegerField('预先提醒', default=0)
    public = models.BooleanField('公共事件', default=False)

    class Meta:
        verbose_name = '事件'
        verbose_name_plural = '日程'

