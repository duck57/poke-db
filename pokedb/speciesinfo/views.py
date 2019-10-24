from django.shortcuts import render
from django.http import HttpResponse


# Create your views here.


def nothing(request, **kwargs):
    return HttpResponse("I'll implement this later.", status=501)
