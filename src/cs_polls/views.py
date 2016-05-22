from django.shortcuts import render, redirect
from django.utils.translation import ugettext_lazy as _
from viewpack import CRUDViewPack, DetailView,  view
from cs_polls import models


class PollCRUD(CRUDViewPack):
    model = models.Poll
    template_extension = '.jinja2'
    template_basename = 'cs_polls/'
    check_permissions = False
    raise_404_on_permission_error = True
    context_data = {
        'content_color': "#9cbc58",
        'object_name': _('poll'),
    }
    exclude_fields = []

    class ResultView(CRUDViewPack.DetailView):
        pattern = r'^(?P<pk>\d+)/result/'

    class DetailViewMixin:
        def post(self, request, *args, **kwargs):
            poll = self.object = self.get_object()

            if poll.can_vote(request.user):
                if poll.alternative_vote:
                    choice_list = self.get_choice_list(request.POST)
                    poll.register_vote(request.user, choice=choice_list)
                else:
                    choice = int(request.POST['choice'][7:])
                    poll.register_vote(request.user, choice=choice)
                return redirect('./result')
            else:
                self.has_vote_error = True
                return self.get(request, *args, **kwargs)

        def get_context_data(self, **kwargs):
            return super().get_context_data(
                has_vote_error=getattr(self, 'has_vote_error', False),
                **kwargs
            )

        def get_choice_list(self, D):
            """
            Return a list of choices from the given alternatives.
            """

            return {
                int(k[7:]): int(v)
                for (k, v) in D.items()
                if k.startswith('option-') and v
            }

