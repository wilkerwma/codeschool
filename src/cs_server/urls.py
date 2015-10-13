from django.conf.urls import url

from . import views

urlpatterns = [
    # Index
    url(r'^$', views.index, name='index'),

    # View question content and submit form
    url(r'^questions/(?P<question_id>[0-9]+)/$',
        views.question, name='question'),

    # View question content and submit form
    url(r'^notas/$', views.grades, name='grades'),

    # View a CSV for all grades
    url(r'^_grades.csv/$', views.grades_csv, name='grades_csv'),
]
