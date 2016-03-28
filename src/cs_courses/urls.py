from django.conf.urls import url, include
from . import views

urlpatterns = [
    url('^$', views.index, name='course-list'),
    url('^discipline/(\d+)/$', views.discipline_detail, name='discipline-detail'),
    url('^detail/(\d+)/$', views.course_detail, name='course-detail'),
    url('^activity/(\d+)', views.activity_detail, name='activity-detail'),
    url('^add-activities/(\d+)$', views.add_activities, name='course-add-activities'),
]
