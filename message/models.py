#coding=utf-8
"""

"""
from django.db import models
from django.conf import settings
from django.core.mail import send_mail, EmailMessage

from multiprocessing import Process 

class Mail(models.Model):
    '''邮件'''
    creator = models.CharField(max_length=256, null=True)

    sender = models.CharField(max_length=256, null=True)
    receiver = models.CharField(max_length=256, null=False)
    subject = models.CharField(max_length=256, null=False)
    content = models.TextField(null=False)
    attach = models.TextField(null=True)

    mail_type = models.CharField(max_length=10, null=False, default="default")
    desc = models.TextField(null=True)
    add_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name='ERP邮件'
        verbose_name_plural='ERP邮件日志'

    def send(self, handler):
        try:
            self.sender = settings.EMAIL_HOST_USER
            self.save()
            
            receiver = self.receiver.split(',')
            msg = EmailMessage(self.subject, self.content, self.sender, receiver)
            msg.content_subtype = "html"  # 主内体现在变成 text/html
            if self.attach:
                attachs = self.attach.split(';')
                for attach in attachs:
                    msg.attach_file(attach)
            # msg.send()
            child_proc = Process(target=msg.send)  
            child_proc.start() 
        except:
            return False
        return True

