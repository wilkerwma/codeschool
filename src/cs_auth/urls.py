from django.conf.urls import url
from . import views

urlpatterns = [
    url('^$', views.index),
    url('^login/$', views.login),
    url('^register/$', views.register),
    url('^profile/(\w+)/$', views.public_profile),
    url('^edit-profile/$', views.edit_profile),
]
