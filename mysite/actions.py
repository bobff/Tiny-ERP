#coding=utf-8

#coding=utf-8
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.contrib.admin import helpers
from django.contrib.admin.util import get_deleted_objects, model_ngettext
from django.db import router, models
from django.template.response import TemplateResponse
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy, ugettext as _

import csv  
from django.http import HttpResponse

def export_csv_action(modeladmin, request, queryset):
    opts = modeladmin.model._meta
    app_label = opts.app_label
    if request.POST.get('post'):
        etype = request.POST.get('export_type')
        fields = request.POST.getlist('export_field')
        
        if not etype:
            return None
        if etype == 'csv':
            return create_csv(modeladmin.model, fields, queryset)
        
        return None

    if len(queryset) == 1:
        objects_name = force_text(opts.verbose_name)
    else:
        objects_name = force_text(opts.verbose_name_plural)

    title = _("Are you sure?")

    context = {
        "title": title,
        "objects_name": objects_name,
        'queryset': queryset,
        "opts": opts,
        "app_label": app_label,
        'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,

        'fields':modeladmin.model._meta.fields,
        'queryset_len':len(queryset),
        'action':'export_csv_action',
    }

    # Display the confirmation page
    try:
        template = modeladmin.export_selected_confirmation_template
        if not template:
            template = "export_field_confirm.html"
    except:
        template = "export_field_confirm.html"
    return TemplateResponse(request, template, context, current_app=modeladmin.admin_site.name)
export_csv_action.short_description = ugettext_lazy("导出所选的 %(verbose_name_plural)s")

def create_csv(model, fields, queryset):
    ## CSV      
    response = HttpResponse(mimetype='text/csv')  
    response['Content-Disposition'] = 'attachment; filename=%s.csv' % model._meta.verbose_name 
    response.write('\xEF\xBB\xBF') 
    writer = csv.writer(response)  

    if not fields:
        export_fields = model._meta.fields
    else:
        export_fields = []
        for f in model._meta.fields:
            if f.name in fields:
                export_fields.append(f)

    field_names = [f.verbose_name for f in export_fields]
    writer.writerow(field_names)  
    
    for q in queryset:
        values = []
        for f in export_fields:
            values.append(getattr(q, f.name))
        writer.writerow(values)
 
    return response