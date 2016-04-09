from django.conf.urls import url
from . import views

urlpatterns = [
    url('^$', views.index),
    url('^(\d+)/$', views.question_io, name='view-io-question'),
    url('^(\d+)/download/$', views.question_io_download, name='download-io-question'),
]
