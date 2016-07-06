from django.conf.urls import url
from django.views.generic import ListView, DetailView
from .models import BaseBadge, PointBadge, ActionBadge, HybridBadge ,Action, PblUser
from . import views
from django.contrib.auth.models import User
from viewpack import CRUDViewPack

class Leaderboard(ListView):
    model = PblUser
    template_name = 'cs_pbl/leaderboards.jinja2'

    def get_queryset(self):
        return super().get_queryset()

class PointBadgeCRUD(CRUDViewPack):
    model = PointBadge
    template_extension = '.jinja2'
    template_basename = 'cs_pbl/point-badge/'
    context_data = {
        'content_color': "purple",

    }

class ActionBadgeCRUD(CRUDViewPack):
    model = ActionBadge
    template_extension = '.jinja2'
    template_basename = 'cs_pbl/action-badge/'
    context_data = {
        'content_color': "purple",

    }

class HybridBadgeCRUD(CRUDViewPack):
    model = HybridBadge
    template_extension = '.jinja2'
    template_basename = 'cs_pbl/hybrid-badge/'
    context_data = {
        'content_color': "purple",

    }

class ActionCRUD(CRUDViewPack):
    model = Action
    template_extension = '.jinja2'
    template_basename = 'cs_pbl/action/'
    context_data = {
        'content_color': "purple",

    }


urlpatterns = [
    url(r'^$', ListView.as_view(model=BaseBadge, template_name='cs_pbl/gamification_detail.jinja2'), name='gamification-detail'),
    url(r'^point-badge/', PointBadgeCRUD.as_include(namespace='point-badge')),
    url(r'^action-badge/', ActionBadgeCRUD.as_include(namespace='action-badge')),
    url(r'^hybrid-badge/', HybridBadgeCRUD.as_include(namespace='hybrid-badge')),
    url(r'^action/', ActionCRUD.as_include(namespace='action')),
    url(r'^leaderboards', Leaderboard.as_view()),
]
