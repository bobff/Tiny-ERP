# coding: utf-8#
import sys;reload(sys);sys.setdefaultencoding('utf8') #设置全局字符集

from django.db import models
from django.conf import settings

# Create your models here.
class Config(models.Model):
    module  = models.CharField('模块',       max_length=100, choices=tuple([(i,i) for i in settings.INSTALLED_APPS]))
    name    = models.CharField('配置名称',   max_length=100)
    value   = models.CharField('值',         max_length=200)
    remarks = models.TextField('备注', null=True, blank=True)

    class Meta:
        #db_table = 'info'
        verbose_name = '配置'
        verbose_name_plural = '配置'

    def __unicode__(self):  # Python 3: def __str__(self):
        return self.module + '_' + self.name