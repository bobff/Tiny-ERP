from django.contrib import admin
from mysite.actions import export_csv_action
# Register your models here.

from dicts.models import Department

class DepartmentAdmin(admin.ModelAdmin):
    list_display_links = ('code', 'name')
    list_display = ('code','name')
    list_filter = ['code', 'name']
    search_fields = ['code','name']
    ordering = ('code',)
    actions = [export_csv_action]

admin.site.register(Department,DepartmentAdmin)

