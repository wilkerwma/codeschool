from django.utils.translation import ugettext_lazy as _
from viewpack import CRUDViewPack, CRUDWithInheritanceViewGroup
from viewpack.views.childviews import DetailObjectContextMixin, VerboseNamesContextMixin, DetailWithResponseView
from codeschool.models import User
from cs_questions import models
users = User.objects


class QuestionInheritanceCRUD(CRUDWithInheritanceViewGroup):
    """
    Base CRUD that dispatch to a different view depending on the question type.
    """

    model = models.Question
    template_extension = '.jinja2'
    template_basename = 'cs_questions/'
    use_crud_views = True
    exclude_fields = ['status', 'status_changed', 'author_name', 'comment',
                      'owner']
    detail_fields = []
    context_data = {
        'content_color': '#BC5454',
        'object_name': _('question'),
    }


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
            response.question_fallback = self.object
            response.get_feedback(commit=False)
            response.save()
            return response

        def form_valid(self, form):
            return self.form_invalid(form)

    class ListViewMixin:
        def get_queryset(self):
            qs = super().get_queryset()
            return qs.filter(is_active=True)


@QuestionInheritanceCRUD.register
class NumericQuestionViews(QuestionCRUD):
    model = models.NumericQuestion


@QuestionInheritanceCRUD.register
class CodingIoQuestionViews(QuestionCRUD):
    model = models.CodingIoQuestion
    response_model = models.CodingIoResponse
    response_fields = ['source', 'language']
    template_basename = 'cs_questions/io/'