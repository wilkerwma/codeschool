from django.conf.urls import url, include
from cs_courses import views


import srvice
from cs_courses import models


@srvice.api
def ajax(request, *args, **kwargs):
    kwargs['msg'] = 'hello from python!'
    return [args, kwargs]


@srvice.program
def run(client, *args, **kwargs):
    client.alert(args, kwargs)
    client.dialog(html='hello world')


from django.shortcuts import render, get_object_or_404
from django import http


def course_description(request, pk):
    course = get_object_or_404(models.Course, pk=pk)
    return http.HttpResponse(course.long_description_html)

urlpatterns = [
    url(r'^ajax/$', ajax.as_view(login_required=True)),
    url(r'^run/$', run.as_view(login_required=True)),

    url(r'^$', views.course_index, name='list'),
    url(r'^(\d+)/$', views.course_detail, name='detail'),
    url(r'^(\d+)/description/$', course_description, name='description'),
    url(r'^discipline/(\d+)/$', views.discipline_detail, name='detail'),
    url(r'^(\d+)/add-activities/$', views.add_activities, name='add-activities'),
]

