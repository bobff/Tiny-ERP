#coding=utf-8
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response 


def home(request):
    return HttpResponseRedirect('/helpdesk/')

