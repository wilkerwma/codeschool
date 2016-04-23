from django.conf.urls import url
from cs_activities import views


urlpatterns = [
    url('^(.*)$', views.ActivityViews.as_view(), name='activity')
]
