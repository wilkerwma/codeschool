from django.conf.urls import url, include
from cs_auth import views


urlpatterns = [
    url(r'^login/$', views.LoginView.as_view(), name='login'),
    url(r'^', include('userena.urls', namespace=None)),
]
