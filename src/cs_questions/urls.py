from django.conf.urls import url
from cs_questions import views

urlpatterns = [
    url('^', views.QuestionViews.as_include(name='question')),
]
