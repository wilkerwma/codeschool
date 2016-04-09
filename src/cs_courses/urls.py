from django.conf.urls import url, include
from . import views

urlpatterns = [
    url('^$', views.course_index, name='course-list'),
    url('^discipline/(\d+)/$', views.discipline_detail, name='discipline-detail'),
    url('^(\d+)/$', views.course_detail, name='course-detail'),
    url('^activity/(\d+)', views.activity_detail, name='activity-detail'),
    url('^(\d+)/add-activities/$', views.course_add_activities, name='course-add-activities'),
    url('^(\d+)/show-lessons', views.course_lessons, name='course-show-lessons'),
]
