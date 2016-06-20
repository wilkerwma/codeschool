from django.utils.translation import ugettext_lazy as _, ugettext as __
from django.db.models.signals import post_save
from django.dispatch import receiver
from django import forms
from codeschool import models
from codeschool import panels
from codeschool import blocks
from cs_core.models import Activity, Response, ProgrammingLanguage

QUESTION_STEM_BLOCKS = [
    ('paragraph', blocks.RichTextBlock()),
    ('heading', blocks.CharBlock(classname='full title')),
    ('code', blocks.CodeBlock()),
    ('markdown', blocks.MarkdownBlock()),
    # ('html', blocks.RawHTMLBlock()), wait support for bleach?
]


@receiver(post_save, sender='cs_core.Course')
def on_course_save(instance, created, **kwargs):
    if created:
        instance.add_child(instance=QuestionList())


class QuestionList(models.CodeschoolPage):
    """
    Root page for all questions inside a course.
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('title', __('List of questions'))
        kwargs.setdefault('slug', 'questions')
        super().__init__(*args, **kwargs)

    # Wagtail admin
    subpage_types = [
        'cs_questioning.SimpleQuestion',
        'cs_questioning.CodingIoQuestion'
    ]


class Question(Activity):
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

    # Properties
    @property
    def long_description(self):
        try:
            value = str(self.stem)
        except Exception as e:
            value = e
        return self.stem

    def update(self):
        """Tells question object to validate and update any fields necessary
        to fulfill the validation.

        The default implementation is empty. Subclasses may need to implement
        some special logic here.
        """

    def export(self, type=None):
        """Export question to the given data type.

        This method can return NotImplemented to tell that the designated data
        type is not supported."""

        return NotImplemented

    def grade(self, response):
        """Return a Feedback object to the given response."""

        return self.feedback_cls(response, self.answer == response.value)

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

    def get_context(self, request, *args, **kwargs):
        ctx = super().get_context(request, *args, **kwargs)
        ctx['form'] = self.get_response_form(request, *args, **kwargs)
        if request.method == 'POST':
            ctx['response'] = ctx['form'].get_response()
        return ctx

    def get_response_form(self, request, *args, **kwargs):
        """
        Return a ModelForm for a question response.
        """

        raise NotImplementedError(
            'Please implement the get_response_form method in the subclass.'
        )

    def _serve(self, request, *args, **kwargs):
        from cs_questions.views import QuestionInheritanceCRUD

        view = QuestionInheritanceCRUD.as_view(
            dispatch_to='detail',
            initkwargs={'object': self}
        )
        return view(request)

    # Wagtail admin
    parent_page_types = ['QuestionList', 'cs_core.Discipline', 'cs_core.Faculty']
    content_panels = Activity.content_panels + [
        panels.StreamFieldPanel('stem'),
        panels.MultiFieldPanel([
            panels.FieldPanel('author_name'),
            panels.FieldPanel('comments'),
        ], heading=_('Optional information'), classname='collapsible collapsed'),
    ]


class QuestionResponse(Response):
    """
    Proxy class for responses to questions.
    """

    class Meta:
        proxy = True

    question = property(lambda x: x.activity)

    @question.setter
    def question(self, value):
        if not isinstance(value, Question):
            type_name = type(value).__name__
            raise TypeError('invalid question type %s' % type_name)
        self.activity = value

    def __init__(self, *args, **kwargs):
        question = kwargs.pop('question', None)
        kwargs.setdefault('activity', question)
        super().__init__(*args, **kwargs)