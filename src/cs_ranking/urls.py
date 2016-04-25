from django.conf.urls import url

from . import views

app_name = 'cs_ranking'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^([0-9]+)$', views.battle_result, name='result'),
]
