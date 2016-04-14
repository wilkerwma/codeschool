from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse as url_reverse
from model_utils.managers import InheritanceManager
from wagtail.wagtailcore.fields import RichTextField
from codeschool import models
from codeschool.shortcuts import delegation
from cs_courses.models import Discipline
from cs_activities.models import Activity


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
        help_text=_('This optional field points to the discipline that is the '
                    'relevant to question.'),
    )
    owner = models.ForeignKey(
        models.User,
        blank=True,
        null=True,
        help_text=_('User who created or uploaded this question.')
    )
    objects = InheritanceManager()

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


@delegation('question', ['long_description', 'short_description'])
class QuestionActivity(Activity):
    question = models.ForeignKey(Question)

    @property
    def name(self):
        return self.question.title


#
# Derived question types
#
class FreeAnswerQuestion(Question):
    pass


class NumericQuestion(Question):
    answer_start = models.FloatField()
    answer_end = models.FloatField(blank=True, null=True)
    is_exact = models.BooleanField(default=True)


class BooleanQuestion(Question):
    answer_key = models.BooleanField()


class StringMatchQuestion(Question):
    template = models.TextField()
    is_regex = models.BooleanField(default=True)


# Import other default question types
from cs_questions.question_coding_io import models as io