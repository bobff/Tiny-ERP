from django.conf.urls import patterns, include, url
# from helpdesk.views import root
urlpatterns = patterns('helpdesk.views',
    url(r'^$', 'index'),
    url(r'^allot$', 'allot_jump'),
    url(r'^task$', 'operate_jump'),
    
    url(r'^ajax_get_unallot$', 'ajax_get_unallot'),
    url(r'^ajax_get_undo$', 'ajax_get_undo'),
    
    url(r'^stats/apply$', 'stats.apply'),
    url(r'^stats/task$', 'stats.task'),
    url(r'^stats/evaluate$', 'stats.evaluate'),
    url(r'^stats/type$', 'stats.atype'),
    url(r'^stats/work$', 'stats.work'),
    
    url(r'^search$', 'search.search'),

    url(r'^calendar$', 'calendar.scheduling'),
    url(r'^calendar/add$', 'calendar.add'),
    url(r'^calendar/update$', 'calendar.update'),
    url(r'^calendar/delete$', 'calendar.delete'),
    url(r'^calendar/load$', 'calendar.load'),

    url(r'^user/passwd$', 'passwd'),    

    url(r'^(?P<url>.+)', 'root'),
    )