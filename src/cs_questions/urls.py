from django.conf.urls import url
from cs_questions import views

urlpatterns = [
    url('^', views.QuestionInheritanceCRUD.as_include(namespace='question')),
]