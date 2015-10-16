from django.conf.urls import url, include
from . import views

urlpatterns = [
    # Index
    url(r'^$', views.list_questions, name='index'),

    # Authentication
    url('^', include('django.contrib.auth.urls')),

    # New account
    url(r'^new-account/$', views.new_account, name='new account'),

    # Disciplines
    url(r'^disciplines/$', views.list_disciplines, name='disciplines'),
    url(r'^disciplines/(?P<pk>[0-9]+)/$', views.discipline_detail, name='discipline view'),

    # Questions
    url(r'^questions/$', views.list_questions, name='list_questions'),
    url(r'^questions/(?P<question_id>[0-9]+)/$', views.question_detail, name='question_detail'),
    url(r'^questions/(?P<question_id>[0-9]+)/download/$', views.question_download, name='question_detail'),

    # Quizzes
    url(r'^quiz/$', views.quiz_detail, name='quiz_detail'),

    # View question_detail content and submit form
    url(r'^grades/$', views.grades_detail, name='grades'),
    url(r'^grades/grades.csv$', views.grades_csv, name='grades'),
    url(r'^grades/grades_all.csv$', views.grades_all_csv, name='grades'),
]
