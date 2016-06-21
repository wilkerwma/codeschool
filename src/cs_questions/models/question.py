from django.utils.translation import ugettext_lazy as _, ugettext as __
from django import forms
import srvice
from codeschool import models
from codeschool import panels
from codeschool import blocks
from codeschool.shortcuts import render
from cs_core.models import Activity, ResponseItem, ResponseContext, Response
from cs_questions.models import QuestionList


QUESTION_STEM_BLOCKS = [
    ('paragraph', blocks.RichTextBlock()),
    ('heading', blocks.CharBlock(classname='full title')),
    ('code', blocks.CodeBlock()),
    ('markdown', blocks.MarkdownBlock()),
    # ('html', blocks.RawHTMLBlock()), wait support for bleach?
]


# noinspection PyPropertyAccess
class Question(models.RoutablePageMixin, Activity):
    """
    Base abstract class for all question types.
    """

    class Meta:
        abstract = True
        permissions = (("download_question", "Can download question files"),)

    stem = models.StreamField(
        QUESTION_STEM_BLOCKS,
        blank=True,
        null=True,
        verbose_name=_('Question description'),
        help_text=_(
            'Describe what the question is asking and how should the students '
            'answer it as clearly as possible. Good questions should not be '
            'ambiguous.'
        ),
    )
    author_name = models.CharField(
        _('Author\'s name'),
        max_length=100,
        blank=True,
        help_text=_(
            'The author\'s name, if not the same user as the question owner.'
        ),
    )
    comments = models.RichTextField(
        _('Comments'),
        blank=True,
        help_text=_('(Optional) Any private information that you want to '
                    'associate to the question page.')
    )

    @property
    def long_description(self):
        return str(self.stem)

    # Permission control
    def can_edit(self, user):
        """Only the owner of the question can edit it"""
        if user is None or self.owner is None:
            return False
        return self.owner.pk == user.pk

    def can_create(self, user):
        """You have to be the teacher of a course in order to create new
        questions."""

        return not user.courses_as_teacher.empty()

    # Serving pages and routing
    @srvice.route(r'^submit-response/$')
    def respond_route(self, client, **kwargs):
        """
        Handles student responses via AJAX and a srvice program.
        """

        raise NotImplementedError

    @models.route(r'^stats/$')
    def stats_route(self, request, **kwargs):
        """
        Shows the stats for each question.
        """

        data = """<dl>
            <dt>Name<dt><dd>{name}<dd>
            <dt>Best grade<dt><dd>{best}<dd>
            <dt>Responses<dt><dd>{n_responses}<dd>
            <dt>Response items<dt><dd>{n_response_items}<dd>
            <dt>Correct responses<dt><dd>{n_correct}<dd>
            <dt>Mean grade responses<dt><dd>{mean}<dd>
            <dt>Context id</dt><dd>{context_id}</dd>
        </dl>
        """.format(
            context_id=self.default_context.id,
            name=self.title,
            best=self.best_final_grade(),
            mean=self.mean_final_grade(),
            n_correct=self.correct_responses().count(),
            n_response_items=self.response_items().count(),
            n_responses=self.responses.count(),
        )

        # Renders content
        context = {'content_body': data,
                   'content_text': 'Stats'}
        return render(request, 'base.jinja2', context)

    @models.route(r'^responses/')
    def response_list_route(self, request):
        """
        Renders a list of responses
        """

        user = request.user
        context = self.get_context(request)
        items = self.response_items(user=user, context='any')
        items = (x.get_real_instance() for x in items)
        context.update(
            question=self,
            object_list=items,
        )
        return render(request, 'cs_questions/response-list.jinja2', context)

    # Wagtail admin
    parent_page_types = [
        'cs_questions.QuestionList',
        'cs_core.Discipline',
        'cs_core.Faculty'
    ]
    content_panels = Activity.content_panels + [
        panels.StreamFieldPanel('stem'),
        panels.MultiFieldPanel([
            panels.FieldPanel('author_name'),
            panels.FieldPanel('comments'),
        ], heading=_('Optional information'),
           classname='collapsible collapsed'),
    ]


class QuestionResponseItem(ResponseItem):
    """
    Proxy class for responses to questions.
    """

    class Meta:
        proxy = True

    question = property(lambda x: x.response.activity.specific)
    question_id = property(lambda x: x.response.activity_id)

    @property
    def is_correct(self):
        if self.given_grade is None:
            raise AttributeError('accessing attribute of non-graded response.')
        else:
            return self.given_grade == 100

    def __init__(self, *args, **kwargs):
        # Make question an alias to activity.
        question = kwargs.pop('question', None)
        if question is not None:
            kwargs.setdefault('activity', question)
        super().__init__(*args, **kwargs)


def register_response_item(question_class):
    """
    Decorator for a ResponseItem subclass that register a given ResponseItem
    class to the class associated with the decorated Question class.
    """

    if not issubclass(question_class, Question):
        raise TypeError('expect a Question subclass')

    def decorator(item_class):
        if not issubclass(item_class, QuestionResponseItem):
            raise TypeError('expect a QUestionResponseItem subclasss')

        question_class.response_item_class = item_class
        return item_class
    return decorator
