from django.conf.urls import url
from . import views

urlpatterns = [
    url('^$', views.index),
    url('^(\d+)/$', views.question_detail, name='question-detail'),
    url('^(\d+)/([a-z0-9-/]+)/$', views.question_action, name='question-action'),
    url('^new/([a-z0-9-]+)/$', views.question_new, name='question-new'),
]
