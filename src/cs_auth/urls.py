from django.conf.urls import url, include
from userena import urls
from cs_auth import views


urlpatterns = [
    url(r'^login/$', views.login, name='auth-login'),
    url(r'^', include(urls)),
]