from django.conf.urls import patterns, include, url

from django.contrib import admin

from django.contrib.auth.views import login, logout

from django.conf import settings

from mysite.views import home

admin.autodiscover()


urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'mysite.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

   # url(r'^$', 'mysite.views.home', name='home'),
    url(r'^$', home),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^helpdesk/', include('helpdesk.urls')),

    (r'^accounts/login/$',  login, {'template_name':'login.html'}), 
    (r'^accounts/logout/$', logout),
)

urlpatterns += patterns('',
    (r'^site_media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_PATH}),
    (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT}),
)
