from django.contrib import admin

# Register your models here.

from .models import Config

class ConfigAdmin(admin.ModelAdmin):
    list_display_links = ('module', 'name', 'value')
    list_display = ('module','name', 'value')
    list_filter = ['module', 'name']
    search_fields = ['module','name']
    ordering = ('module', 'name')

admin.site.register(Config,ConfigAdmin)
