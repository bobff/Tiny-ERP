#coding=utf-8
from message.models import Mail
from django.conf import settings
from django.template import Context, Template

class ErrorReportMiddleware(object):

    def process_exception(self, request, exception):
        try:
            email = Mail()
            email.subject = str(exception)
            t = Template("{{request|linebreaksbr}}")
            email.content = t.render(Context({'request':request}))
            email.receiver = ','.join(settings.DEVELOPER_MAIL)
            email.creator = str(request.user)
            email.mail_type = 'ERROR'
            email.send('SYS')
        except:
            pass
        return None
