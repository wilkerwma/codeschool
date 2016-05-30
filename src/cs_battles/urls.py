from django.conf.urls import url

from . import views

app_name = 'cs_battles'
urlpatterns = [
    url(r'^',views.BattleCRUDView.as_include(namespace='battles')),
    url(r'^battle/(?P<battle_pk>\d+)$', views.battle, name='battle'),
    url(r'^user$',views.battle_user, name='user_battle'),
    url(r'^accept$',views.battle_invitation,name="accept_battle"),
    url(r'^invitations$',views.invitations, name="view_invitation"),
]
