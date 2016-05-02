from django.conf.urls import url

from . import views

app_name = 'cs_ranking'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^battle/$', views.battle, name='battle'),
    url(r'^battle/([0-9]+)$', views.battle_result, name='result'),
    url(r'^([0-9]+)$', views.battle_result, name='result'),
    url(r'^user$',views.battle_user, name='user_battle'),
    url(r'^accept$',views.battle_invitation,name="accept_battle"),
    url(r'^invitation$',views.invitations, name="view_invitation")
]
