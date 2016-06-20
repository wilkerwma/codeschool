from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^(?P<battle_pk>\d+)/$', views.message_manager),
]
