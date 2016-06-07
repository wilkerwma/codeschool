from django.conf.urls import url
from cs_activities import views


urlpatterns = [
    url('^', views.ActivityCRUD.as_include(namespace='activity'))
]
