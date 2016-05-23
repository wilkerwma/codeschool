from django.conf.urls import url
from django.views.generic import ListView, DetailView
from .models import Badge
from . import views
from django.contrib.auth.models import User
from viewpack import CRUDViewPack

class Leaderboard(ListView):
    model = User
    template_name = 'cs_pbl/leaderboards.jinja2'

    def get_queryset(self):
        return super().get_queryset()

class BadgeCRUD(CRUDViewPack):
    model = Badge
    template_extension = '.jinja2'
    template_basename = 'cs_pbl/badge/'
    context_data = {
        'content_color': "purple",

    }

urlpatterns = [
    url(r'^$', ListView.as_view(model=Badge, template_name='cs_pbl/gamification_detail.jinja2'), name='gamification-detail'),
    url(r'^badge/', BadgeCRUD.as_include(namespace='badge')),
    #url(r'^badge_list', ListView.as_view(model=Badge, template_name='cs_pbl/badge_list.jinja2'), name='badge-list'),
    #url(r'^badge_detail/(?P<pk>\d+)/$', DetailView.as_view(model=Badge, template_name='cs_pbl/badge_detail.jinja2'), name='badge-detail'),
    #url(r'^leaderboards', ListView.as_view(model=User, template_name='cs_pbl/leaderboards.jinja2'),name='leaderboards'),
    url(r'^leaderboards', Leaderboard.as_view()),
]
