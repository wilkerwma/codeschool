from django.utils.translation import ugettext_lazy as _, ugettext as __
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.html import escape
from codeschool import models
from codeschool.shortcuts import render, render_html
from cs_core import models as core_models


@receiver(post_save, sender='cs_core.Course')
def on_course_save(instance, created, **_):
    if created:
        instance.add_child(instance=QuestionList())
        instance.add_child(instance=QuizList())


class QuestionList(models.RoutablePageMixin, models.RootList):
    """
    Root page for all questions inside a course.
    """

    class Meta:
        proxy = True

    @property
    def questions(self):
        return [x.specific for x in self.get_children()]

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('title', __('List of questions'))
        kwargs.setdefault('slug', 'questions')
        super().__init__(*args, **kwargs)

    def get_gradebook(self, user):
        """
        Return a gradebook object with the grades associated to all questions
        registered in the course which were submited using the default context.
        """

        questions = [question.specific for question in self.get_children()]
        return UserGradebook(questions, user)

    # Serving and routes
    @models.route(r'^grades/$')
    def route_gradebook(self, request):
        user = request.user
        gradebook = self.get_gradebook(user)
        gradebook.title = _('Gradebook')
        context = {
            'object': gradebook,
            'short_description': gradebook.title,
            'long_description': _('List of grades'),
            'detail_object': gradebook,
            'verbose_name': _('Gradebook'),
        }
        template = 'cs_questions/user_gradebook.jinja2'
        return render(request, template, context)

    # Wagtail admin
    subpage_types = [
        'cs_questions.FormQuestion',
        'cs_questions.CodingIoQuestion'
    ]


class QuizList(models.RootList):
    """
    Root page for all quizzes inside a course.
    """

    class Meta:
        proxy = True

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('title', __('Quizzes'))
        kwargs.setdefault('slug', 'quizzes')
        super().__init__(*args, **kwargs)

    # Wagtail admin
    subpage_types = [
        'cs_questions.Quiz',
    ]


#
# Gradebook object (move somewhere else)
#
class UserGradebook:
    def __init__(self, questions, user):
        self.questions = questions
        self.user = user

    def __iter__(self):
        user = self.user
        for question in self.questions:
            response = question.get_response(user)
            attempts = response.num_attempts
            response.update(force=True)
            grade = response.final_grade
            url = question.get_absolute_url()
            title = escape(question.title)
            question_link = '<a href="%s">%s</a>' % (url, title)
            yield (question_link, attempts, '%.1f%%' % grade)

    def render(self):
        head = _('Question'), _('# attempts'), _('Final grade')
        lines = [
            '<table class="gradebook">',
            '<thead>',
            '<tr><th>%s</th><th>%s</th><th>%s</th></tr>' % head,
            '</thead>',
            '<tbody>',
        ]
        for (question, N, grade) in self:
            line = question, N, grade
            line = ''.join('<td>%s</td>' % elem for elem in line)
            line = '<tr>%s</tr>' % line
            lines.append(line)
        lines.extend([
            '</tbody>',
            '</table>'
        ])
        return '\n'.join(lines)

    def __html__(self):
        return self.render()

    def __str__(self):
        return self.render()