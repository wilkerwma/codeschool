from django.conf.urls import url
from . import views

urlpatterns = [
    url('^$', views.index),
    url('^(\d+)/$', views.question_io),
]
