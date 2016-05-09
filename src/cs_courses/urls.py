from django.conf.urls import url, include
from . import views

urlpatterns = [
    url('^$', views.course_index, name='course-list'),
    url('^(\d+)/$', views.course_detail, name='course-detail'),
    url('^discipline/(\d+)/$', views.discipline_detail, name='discipline-detail'),
    url('^(\d+)/add-activities/$', views.add_activities, name='course-add-activities'),
]
