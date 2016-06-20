import decimal
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from codeschool import models
from codeschool import blocks
from cs_core.models.activity import Activity


def grading_method_best():
    """
    Return the "best" GradingMethod instance.
    """

    from cs_core.models import GradingMethod
    return GradingMethod.best().pk


class ResponseContext(models.PolymorphicModel):
    """
    Define a different context for a response object.

    The context group responses into explicit groups and may also be used to
    define additional constraints on the correct answers.
    """

    class Meta:
        unique_together = [('activity', 'name')]

    # Basic
    activity = models.ParentalKey(
        'wagtailcore.Page',
        related_name='contexts',
    )
    name = models.CharField(
        _('name'),
        max_length=140,
        blank=True,
        help_text=_(
            'A unique identifier.'
        )
    )
    description = models.RichTextField(
        _('description'),
        blank=True,
    )

    # Grading and submissions
    grading_method = models.ForeignKey(
        'cs_core.GradingMethod',
        on_delete=models.SET_DEFAULT,
        default=grading_method_best,
        blank=True,
        help_text=_('Choose the strategy for grading this activity.')
    )
    single_submission = models.BooleanField(
        _('single submission'),
        default=False,
        help_text=_(
            'If set, students will be allowed to send only a single response.',
        ),
    )

    # Feedback
    delayed_feedback = models.BooleanField(
        _('delayed feedback'),
        default=False,
        help_text=_(
            'If set, students will be only be able to see the feedback after '
            'the activity expires its deadline.'
        )
    )

    # Deadlines
    deadline = models.DateTimeField(
        _('deadline'),
        blank=True,
        null=True,
    )
    hard_deadline = models.DateTimeField(
        _('hard deadline'),
        blank=True,
        null=True,
        help_text=_(
            'If set, responses submitted after the deadline will be accepted '
            'with a penalty.'
        )
    )
    delay_penalty = models.DecimalField(
        _('delay penalty'),
        default=25,
        decimal_places=2,
        max_digits=6,
        help_text=_(
            'Sets the percentage of the total grade that will be lost due to '
            'delayed responses.'
        ),
    )

    # Programming languages/formats
    format = models.ForeignKey(
        'cs_core.FileFormat',
        blank=True,
        null=True,
        help_text=_(
            'Defines the required file format or programming language for '
            'student responses, when applicable.'
        )
    )

    # Extra constraints and resources
    constraints = models.StreamField([], default=[])
    resources = models.StreamField([], default=[])

    def clean(self):
        if not isinstance(self.activity, Activity):
            return ValidationError({
                'parent': _('Parent is not an Activity subclass'),
            })
        super().clean()

