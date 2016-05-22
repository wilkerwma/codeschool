from django.conf.urls import url

from . import views

app_name = 'cs_ranking'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^battle/(?P<battle_pk>\d+)$', views.battle, name='battle'),
    url(r'^battle/(?P<battle_pk>\d+)/result/$', views.battle_result, name='result'),
    url(r'^([0-9]+)$', views.battle_result, name='result'),
    url(r'^user$',views.battle_user, name='user_battle'),
    url(r'^accept$',views.battle_invitation,name="accept_battle"),
    url(r'^invitations$',views.invitations, name="view_invitation"),
    url(r'^invitation$',views.invitation_users,name="invitation_users"),
]
