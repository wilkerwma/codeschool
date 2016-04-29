from django.utils.translation import ugettext_lazy as _
from viewgroups import CRUDViewGroup, CRUDWithInheritanceViewGroup
from codeschool.models import User
from cs_questions import models
from cs_questions import forms
users = User.objects


class QuestionViews(CRUDWithInheritanceViewGroup):
    model = models.Question
    template_extension = '.jinja2'
    template_basename = 'cs_questions/'
    use_crud_views = True
    exclude_fields = ['status', 'status_changed', 'author_name', 'comment', 'owner']
    detail_fields = []
    context_data = {
        'content_color': '#BC5454',
        'object_name': _('question'),
    }


@QuestionViews.register
class NumericQuestionViews(CRUDViewGroup):
    model = models.NumericQuestion


@QuestionViews.register
class CodingIoQuestionViews(CRUDViewGroup):
    model = models.io.CodingIoQuestion
    template_base = 'cs_questions/io/'

    class DetailViewMixin:
        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context['form'] = forms.CodingIoResponseForm()
            return context

class fpp:
    """
    Base mapper for all Question view subtypes.
    """

    template_root = 'cs_questions/'
    object_varname = 'question'
    model_form_excludes = (
        'id', 'question_ptr', 'modified', 'created', 'comment', 'author_name',
        'owner', 'status', 'status_changed',
   )
    response_form_excludes = (
        'id', 'created', 'modified', 'status', 'status_changed', 'activity',
        'group', 'user', 'response_ptr'
    )

    def finalize(self, obj):
        obj.update()

    def view_detail(self, obj):
        """The details page for question: it shows description and a form for
        the user to submit its responses.

        This method that the class attribute response_form should hold a django
        form class that processes form inputs."""

        request = self.request
        self.context.update({
            'grade': None,
            'feedback': None,
            'can_download': obj.can_edit(request.user),
        })
        context = self.context
        activity = None

        if request.method == 'POST':
            form = self.response_form(request.POST)
            if form.is_valid():
                response = form.save(commit=False)
                response.user = request.user
                response.activity = activity
                response.save()

                # Grade it and save feedback
                feedback = obj.grade(response)
                feedback.save()
                context['grade'] = int(feedback.grade * 100)
                context['feedback'] = feedback

        self.fsetdefault('form', self.response_form)
        return self.render(self.detail_template, obj)



# Import views from other modules
#from cs_questions.question_coding_io.views import CodingIoQuestionViews
