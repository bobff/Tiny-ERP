# coding: utf-8#
import sys;reload(sys);sys.setdefaultencoding('utf8') #设置全局字符集

import datetime
from django.utils import timezone
from django.db import models


# Create your models here.
class Department(models.Model):
    code = models.CharField('部门编号', max_length=10, primary_key=True)
    name = models.CharField('部门名称', max_length=100)
    class Meta:
        #db_table = 'info'
        verbose_name = '部门'
        verbose_name_plural = '部门'

    def __unicode__(self):  # Python 3: def __str__(self):
        return self.name


