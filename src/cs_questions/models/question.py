from django.utils.translation import ugettext_lazy as _, ugettext as __
from django import forms
import srvice
from codeschool import models
from codeschool import panels
from codeschool import blocks
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
