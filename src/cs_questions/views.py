from codeschool.models import User
from codeschool.shortcuts import render
from codeschool.urlsubclassmapper import URLSubclassMapper, ViewMapper, auto_form
from cs_questions import models
users = User.objects


mapper = URLSubclassMapper(models.Question.objects)


def index(request):
    """List of all public questions."""

    questions = models.Question.objects.all().order_by('pk')
    context = {'questions': questions}
    return render(request, 'cs_questions/index.jinja2', context)


class QuestionViews(ViewMapper):
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
    response_form = auto_form('model.response_cls')

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


@mapper.register(model=models.NumericQuestion, name='numeric')
class NumericQuestionViews(QuestionViews):
    response_form_includes = ['value']


# Import views from other modules
from cs_questions.question_coding_io.views import CodingIoQuestionViews
