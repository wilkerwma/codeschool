from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse as url_reverse
from model_utils.managers import InheritanceManager
from codeschool import models
from codeschool.shortcuts import delegation
from cs_courses.models import Discipline
from cs_activities.models import Activity, Response


class Question(models.TimeStampedModel):
    """Base class for all question types"""

    title = models.CharField(
        _('title'),
        max_length=200,
    )
    short_description = models.CharField(
        _('short description'),
        max_length=140,
        help_text=_('A very brief one-phrase description used in listings.'),
    )
    long_description = models.TextField(
        _('long description'),
        help_text=_('A detailed explanation.')
    )
    author_name = models.CharField(
        _('Author\'s name'),
        max_length=100,
        blank=True,
    )
    comment = models.TextField(
        _('Comments'),
        blank=True,
        help_text=_('(Optional) Any private information that you want to '
                    'associate to the object.')
    )
    discipline = models.ForeignKey(
        Discipline,
        blank=True,
        null=True,
        help_text=_(
            'This optional field points to the discipline that is the relevant '
            'to question.'
        ),
    )
    owner = models.ForeignKey(
        models.User,
        blank=True,
        null=True,
        help_text=_('User who created or uploaded this question.')
    )
    is_active = models.BooleanField(
        _('is active'),
        default=False,
        blank=True,
        help_text=_(
            'Marks a question as active/inactive. Inactive questions are not'
            'shown publicly and are only available to the question owner.'
        )
    )

    # Manager
    objects = InheritanceManager()
    response_cls = Response
    default_extension = '.md'

    @property
    def responses(self):
        return getattr(self, self.response_cls.__name__.lower() + '_set')

    class Meta:
        permissions = (("download_question", "Can download question files"),)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return url_reverse('question-detail', args=(self.pk,))

    def can_edit(self, user):
        """Return True if user can edit question."""

        if user is None or self.owner is None:
            return False
        return self.owner.pk == user.pk

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


@delegation('question', ['long_description', 'short_description'])
class QuestionActivity(Activity):
    question = models.ForeignKey(Question)

    @property
    def name(self):
        return self.question.title


class QuestionResponse(Response):
    question = models.ForeignKey(Question, blank=True, null=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if self.question is None:
            self.question = self.activity.question
        return super().save(*args, **kwargs)


#
# Derived question types
#
class FreeAnswerQuestion(Question):
    DATA_FILE = 'file'
    DATA_IMAGE = 'image'
    DATA_PDF = 'pdf'
    DATA_PLAIN = 'plain'
    DATA_RICHTEXT = 'richtext'
    DATA_CHOICES = (
        (DATA_FILE, _('Arbitary file')),
        (DATA_IMAGE, _('Image file')),
        (DATA_PDF, _('PDF file')),
        (DATA_RICHTEXT, _('Rich text input')),
        (DATA_RICHTEXT, _('Plain text input')),
    )
    metadata = models.TextField()
    data_type = models.CharField(choices=DATA_CHOICES, max_length=10)
    data_file = models.FileField(blank=True, null=True)


class NumericResponse(QuestionResponse):
    value = models.FloatField(
        _('Value'),
        help_text=_('Result (it must be a number)')
    )


class NumericQuestion(Question):
    answer = models.FloatField(
        _('Answer'),
        help_text=_('The numeric value for the correct answer')
    )
    tolerance = models.FloatField(
        _('Tolerance'),
        help_text=_('If given, defines the tolerance within responses are '
                    'still considered to be correct'),
        default=0,
        blank=True,
    )

    response_cls = NumericResponse

    @property
    def is_exact(self):
        return self.tolerance == 0

    @property
    def start(self):
        return self.answer - abs(self.tolerance)

    @property
    def end(self):
        return self.answer + abs(self.tolerance)

    @property
    def range(self):
        return self.start, self.end

    def grade(self, response):
        x, y = self.range
        response.grade = (100 if x <= response.value <= y else 0)
        response.save()


class BooleanQuestion(Question):
    answer = models.BooleanField()


class StringMatchQuestion(Question):
    answer = models.TextField()
    is_regex = models.BooleanField(default=True)

    def grade(self, response):
        if self.is_regex:
            value = response.value

        else:
            return super().grade(response)

# Import other question types
from cs_questions.models_io import *
