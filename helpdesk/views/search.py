import sys

from django.db.models.base import ModelBase
from django.db.models.fields import *
from django.db.models import Q

from . import login_required
from .. import get_role
from utils import dispatch_url, render_to_response

from helpdesk import models as helpdesk_models

search_models = (helpdesk_models, )

@login_required
def search(request):
    q = request.GET.get('q','')
    refine = request.GET.get('r')
    if refine != 'on':
        refine = False
    else:
        refine = True
    dicts = get_role(request)
    dicts['q'] = q
    if q != None and q != '':
        res = {}
        for appmodel in search_models:
            for item in appmodel.__dict__.items():
                if type(item[1]) == ModelBase and item[1].__module__ == appmodel.__name__:
                    model = item[1]
                    args = []
                    for i in model._meta.fields:
                        if type(i) in (IPAddressField, TextField, CharField, EmailField):
                            if not refine:
                                tmp = {i.name + '__contains' : q}
                            else:
                                tmp = {i.name : q}
                            args.append(Q(**tmp))  
                    if len(args) > 1:
                        bob = args[0] 
                        for i in range(1,len(args)):
                            bob = bob | args[i]
                        obj = model.objects.filter(bob)
                        fields = []
                        table_width = 0
                        for field in model._meta.fields:
                            if type(field) == TextField:
                                fields.append((field.verbose_name,200))
                                table_width += 200
                            else:
                                fields.append((field.verbose_name,100))
                                table_width += 100
                        rows = []
                        for o in obj:
                            values = []
                            for field in model._meta.fields:
                                if type(field) == related.ForeignKey:
                                    values.append(getattr(o, field.name + '_id'))
                                else:
                                    values.append(getattr(o, field.name))
                            rows.append(values)
                        if len(rows) > 0:
                            res[model._meta.verbose_name] = {
                                'fields':fields, 
                                'rows':rows, 
                                'table_width': table_width, 
                                'base_url':'/admin/' + appmodel.__package__ + '/' + model.__name__.lower()}
        dicts['res'] = res
    return render_to_response(request, 'search.html', dicts)
    