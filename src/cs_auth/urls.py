from django.conf.urls import url, include
from cs_auth import views


urlpatterns = [
    url(r'^login/$', views.login, name='login'),
    url(r'^', include('userena.urls', namespace=None)),
]
