from django.contrib import admin

# Register your models here.

from helpdesk.models import HelpDeskUser, Application, ApplyType, Task


class HelpDeskUserAdmin(admin.ModelAdmin):
    list_display_links = ('id','user','department','role','duty', 'email', 'phone', 'mobile', 'address')
    list_display = ('id','user','department','role','duty', 'email', 'phone', 'mobile', 'address')
    list_filter = ['department','duty','role']
    search_fields =  ['user__username','department__name','duty','role', 'email', 'phone', 'mobile', 'address']
    ordering = ('user__username',)
admin.site.register(HelpDeskUser, HelpDeskUserAdmin)

class ApplicationAdmin(admin.ModelAdmin):
    list_display_links = ('uuid', 'name', 'department', 'email', 'status', 'apply_time', 'view_time', 'evaluation')
    list_display = ('uuid', 'name', 'department', 'email', 'status', 'apply_time','view_time', 'evaluation', 'category')
    list_filter = ['category', 'name', 'department', 'status', 'evaluation']
    search_fields = ('uuid', 'name', 'department__name', 'email', 'status')
    ordering = ('-apply_time',)
    def get_readonly_fields(self, request, obj=None):
        return [ field.name for field in Application._meta.fields]
        # return ['apply_time', 'view_time', 'finish_time', 'evaluate_time']
admin.site.register(Application,ApplicationAdmin)

class ApplyTypeAdmin(admin.ModelAdmin):
    list_display_links = ('uuid', 'type')
    list_display = ('uuid', 'type')
    list_filter = ['type']
    search_fields = ['uuid__uuid', 'type']
    ordering = ('type',)
admin.site.register(ApplyType, ApplyTypeAdmin)

class TaskAdmin(admin.ModelAdmin):
    list_display_links = ( 'uuid', 'alloter', 'allot_time', 'operator_duty', 'operator', 'operate_time', 'result')
    list_display = ( 'uuid', 'alloter', 'allot_time', 'operator_duty', 'operator', 'operate_time', 'result')
    list_filter = ['uuid__category', 'result', 'alloter', 'operator_duty', 'operator']
    search_fields = ['uuid', 'alloter', 'operator_duty', 'operator',]
    ordering = ('-allot_time',)

    def get_readonly_fields(self, request, obj=None):
        return [ field.name for field in Task._meta.fields]
admin.site.register(Task, TaskAdmin)

