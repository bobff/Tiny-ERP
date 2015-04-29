#coding=utf-8

"""
该模块包含系统开发Web视图开发框架

@version: $Id$
@author: U{gaobo<mailto:gaobo@bjtu.edu.cn>}, U{jesuit}
@contact: gaobo@bjtu.edu.cn
@see: 参考资料链接等等
@license: GPL
@todo:
@bug:

"""
import re
from datetime import datetime

#import ho.pisa as pisa
import cStringIO as StringIO
import cgi
import csv

from django.forms import ModelForm
from django.forms.models import model_to_dict
from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponse, Http404, HttpResponseBadRequest
from django.template.loader import get_template
from django.template import Context

from utils import get_page, render_to_response, get_rand_str, get_abs_attach_fname, render_to_response_json

class AbsView(object):
    """
    Web视图框架的抽象类，对于一般的对象操作包含基本操作CRUD，即所谓的新建、删除、修改、查询。该类
     基于此种思想，抽象出对于对象的的基本操作，置于视图之中，并加入url配置与转发。
    """
    
    DefaultModel = None
    """
    每个view会对应一个所操作的model。
    """    
    urlmap = {}
    """
    url配置
    """
    template_dir = ""
    """
    模板目录
    """
    csv_columns = None
    '''
    导出excel的表头文件
    '''
    
    def root(self, request, url):
        """
        解析、转发url到相应的函数中，若没有对应的配置，返回404错误。
        """
        
        for key in self.urlmap.keys():
            
            m = re.match(key, url)
            
            if m:
                mflag = True
                fun_name = self.urlmap[key][0]
                template = self.urlmap[key][1]
                
                if not template:
                    template = fun_name
                    
                template = "%s%s.html" %(self.template_dir, template)
                
                try:
                    func =  self.__getattribute__(fun_name)
                except:
                    func = None
                
                if func and callable(func):
                    return func(request, template, **(m.groupdict()))

        raise Http404

    def list(self, request, template):
        '''
           抽象方法，处理对象列表与对象搜索。
        '''
        raise NotImplementedError("abstract")
    
    def add(self, request, template):
        '''
           抽象方法，处理对象新建。
        '''
        raise NotImplementedError("abstract")
    
    def update(self, request, id, template):
        '''
           抽象方法，处理对象更新。
        '''
        raise NotImplementedError("abstract")
    
    def view(self, request, id, template):
        '''
           抽象方法，处理单一对象显示。
        '''
        raise NotImplementedError("abstract")
    
    def delete(self, request, id, template):
        '''
           抽象方法，处理单一对象删除。
        '''
        raise NotImplementedError("abstract")
    
    def query(self, request, template):
        '''
           抽象方法，显示查询页面。
        '''
        raise NotImplementedError("abstract")
    
    def csv_export(self, request, p_list, cols = None):
        '''
           处理对象列表时，做excel输出。
        '''
        
        def u2g(str):
            return str.decode('utf-8').encode('gb18030')
    
        def d2g(string):
            try:
                string.decode('utf-8').encode('gb18030')
            except:
                try:
                   string = string.encode('gb18030') 
                except:
                    pass
            return str(string)
        
        def get_csv_cell(p, k, index):
            if k == "forloop.count":
                return str(index+1)
            if type(k)==list:
                value = p
                for key in k:
                    if hasattr(value, key):
                        value = getattr(value,key)
                        if callable(value): value = value()
                    else:
                        value=""
                        break
                return  d2g(value)
            else:
                if hasattr(p, k):
                    value = getattr(p, k)
                    if callable(value): value = value()
                    return d2g(value)
                else:
                    return ""
                
        # Create the HttpResponse object with the appropriate CSV header.
        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename=excel.csv'
        writer = csv.writer(response)
        
        if cols:
            csv_columns = []
            for i in self.csv_columns:
                if i[0].decode("utf-8") in cols:
                    csv_columns.append(i)
        else:
            csv_columns = self.csv_columns

        writer.writerow([u2g(i) for i, j in csv_columns])
        for index, p in enumerate(p_list):            
            re_list = [get_csv_cell(p, j, index) for i, j in csv_columns]
            writer.writerow(re_list)
               
        return response 
    