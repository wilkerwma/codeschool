from django.conf.urls import url
from . import views

urlpatterns = [
    url('^$', views.index, name='linktable-index'),
    url('^(\d+)/$', views.linktable, name='linktable-detail'),
]
