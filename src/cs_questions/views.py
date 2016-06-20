from django.utils.translation import ugettext_lazy as _
from viewpack import CRUDViewPack, InheritanceCRUDViewPack, DispatchView
from viewpack.permissions import can_download, can_edit
from viewpack.views import DetailWithResponseView, ListView, DetailView
from viewpack.views.mixins import (DetailObjectContextMixin,
                                   VerboseNamesContextMixin)
from codeschool.utils import lazy
from codeschool.models import User
from cs_questions import models

users = User.objects


class QuestionDetailView(DetailObjectContextMixin,
                         VerboseNamesContextMixin,
                         DetailWithResponseView):
    """Base detail view class for question types.

    This view can be plugged and reused in the many places that a question
    detail view may be used inside codeschool."""

    @property
    def question(self):
        return self.object

    @question.setter
    def question(self, value):
        self.object = value

    @lazy
    def activity(self):
        return self.get_activity()

    @lazy
    def programming_languages(self):
        return self.get_programming_languages()

    def get_activity(self):
        """Return the activity object in the context of this question."""

        try:
            pk = self.request.GET['activity']
            self.activity = models.Activity.objects.get_subclass(pk=pk)
        except KeyError:
            self.activity = None
        return self.activity

    def get_programming_languages(self):
        """Return the programming language object for this question.

        This is only relevant for coding questions that permit to select a
        programming language."""

        self.programming_languages = None
        if self.activity is not None and self.activity.language:
                self.programming_languages = [self.activity.language]
        return self.programming_languages

    def get_response(self, form):
        """Return the response object from a valid response form."""

        register = lambda user, r: None
        params = self.request.GET

        # Quiz activity responses
        if 'activity' in params:
            pk = params['activity']
            activity = models.Activity.objects.get_subclass(pk=pk)
            register = activity.register_response
            if activity.status != activity.STATUS_OPEN:
                raise RuntimeError('quiz does not accept responses.')

        # Question activities responses
        elif 'activity' in params:
            raise NotImplementedError

        response = form.save(commit=False)
        response.user = self.request.user
        response.question = self.question
        response.autograde_response()
        register(self.request.user, response)
        return response

    def form_valid(self, form):
        return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        user = self.request.user
        obj = self.object
        return super().get_context_data(
            can_edit=can_edit(obj, user),
            can_download=can_download(obj, user),
            activity=self.activity,
            programming_languages=self.programming_languages,
            question=self.question,
            **kwargs
        )


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

    def set_owner(self, object, user):
        """Sets the owner for the given object."""

        object.owner = user
        object.save(update_fields=['owner'])


class QuestionCRUD(CRUDViewPack):
    """
    Base CRUD functionality to all question types.

    We replace the default DetailView for a DetailWithResponseView in order to
    enable a response form in the detail page of each object.
    """

    class DetailView(QuestionDetailView):
        pattern = r'^(?<pk>\d+)/$'

    class ResponseListView(VerboseNamesContextMixin, ListView):
        pattern = r'(?P<pk>\d+)/responses/'
        view_name = 'response-list'

        @property
        def model(self):
            return self.parent.model.response_cls

        def get_queryset(self):
            question = self.parent.object
            return question.unbound_responses.filter(user=self.request.user)


@QuestionInheritanceCRUD.register
class CodingIoQuestionViews(QuestionCRUD):
    subclass_view_name = 'io'
    model = models.CodingIoQuestion
    response_model = models.CodingIoResponseItem
    response_fields = ['source', 'language']
    template_basename = 'cs_questions/io/'
    upload_enable = True
    upload_success_url = '/questions/{object.pk}/edit/'
