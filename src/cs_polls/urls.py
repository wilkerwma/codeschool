from django.conf.urls import url
from cs_polls import views


urlpatterns = [
    url('^', views.PollCRUD.as_include(namespace='poll'))
]
