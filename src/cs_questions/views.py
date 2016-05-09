from django.utils.translation import ugettext_lazy as _

from codeschool.models import User
from cs_questions import models
from viewpack import CRUDViewPack, InheritanceCRUDViewPack, DispatchView
from viewpack.permissions import can_download, can_edit
from viewpack.views.childviews import (
    DetailObjectContextMixin, VerboseNamesContextMixin,
    DetailWithResponseView, ListView
)

users = User.objects


class QuestionInheritanceCRUD(InheritanceCRUDViewPack):
    """
    Base CRUD that dispatch to a different view depending on the question type.
    """

    model = models.Question
    template_extension = '.jinja2'
    template_basename = 'cs_questions/'
    check_permissions = True
    raise_404_on_permission_error = True
    exclude_fields = ['status', 'status_changed', 'author_name', 'comment',
                      'owner']
    detail_fields = []
    context_data = {
        'content_color': '#BC5454',
        'object_name': _('question'),
    }

    def can_view(self, object):
        return True

    class ListView(InheritanceCRUDViewPack.ListView):
        def get_queryset(self):
            return super().get_queryset().filter(is_active=True)

    class ResponseListView(DispatchView):
        pattern = r'(?P<pk>\d+)/responses/'
        view_name = 'response-list'


class QuestionCRUD(CRUDViewPack):
    """
    Base CRUD functionality to all question types.

    We replace the default DetailView for a DetailWithResponseView in order to
    enable a response form in the detail page of each object.
    """

    class DetailView(DetailObjectContextMixin,
                     VerboseNamesContextMixin,
                     DetailWithResponseView):
        pattern = r'^(?<pk>\d+)/$'

        def get_response(self, form):
            response = form.save(commit=False)
            response.user = self.request.user
            response.question = self.object
            response.get_feedback(commit=False)
            response.save()
            return response

        def form_valid(self, form):
            return self.form_invalid(form)

        def get_context_data(self, **kwargs):
            user = self.request.user
            obj = self.object
            return super().get_context_data(
                can_edit=can_edit(obj, user),
                can_download=can_download(obj, user),
                **kwargs
            )

    class ResponseListView(VerboseNamesContextMixin, ListView):
        pattern = r'(?P<pk>\d+)/responses/'
        view_name = 'response-list'

        @property
        def model(self):
            return self.parent.model.response_cls

        def get_queryset(self):
            question = self.parent.object
            return question.responses.filter(user=self.request.user)


@QuestionInheritanceCRUD.register
class NumericQuestionViews(QuestionCRUD):
    model = models.NumericQuestion


@QuestionInheritanceCRUD.register
class CodingIoQuestionViews(QuestionCRUD):
    subclass_view_name = 'io'
    model = models.CodingIoQuestion
    response_model = models.CodingIoResponse
    response_fields = ['source', 'language']
    template_basename = 'cs_questions/io/'