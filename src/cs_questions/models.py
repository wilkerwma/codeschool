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
        help_text=_('The short description is used in listings and should '
                    'present a brief one phrase description of the question.'),
    )
    long_description = RichTextField(
        _('long description'),
        help_text=_('The long and detailed description of the question that is'
                    'shown in the question submission form. This field '
                    'expects markdown markup.')
    )
    author_name = models.CharField(
        _('Author\'s name'),
        max_length=100,
        blank=True,
    )
    comment = models.TextField(
        _('Comments'),
        blank=True,
        help_text=_('The comments field is for any private information that '
                    'you should want to associate to the object. This field is '
                    'private and its contents are never revealed publicly.')
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