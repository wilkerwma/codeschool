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
        unique_together = [('parent', 'name')]

    # Basic
    parent = models.ParentalKey(
        'wagtailcore.Page',
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
            'the activity deadline.'
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
        if not isinstance(self.parent, (Activity, None.__class__)):
            return ValidationError({
                'parent': _('Parent is not an Activity subclass'),
            })
        super().clean()


class Response(models.CopyMixin,
               models.TimeStampedModel,
               models.PolymorphicModel,
               models.ClusterableModel):
    """
    Gather individual responses.
    """

    class Meta:
        unique_together = [('user', 'activity', 'context')]
        verbose_name = _('final response')
        verbose_name_plural = _('final responses')

    context = models.ForeignKey(
        ResponseContext,
        blank=True,
        null=True,
    )
    activity = models.ForeignKey(
        'wagtailcore.Page',
        related_name='responses',
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        models.User,
        related_name='responses',
    )
    final_grade = models.DecimalField(
        _('Final grade'),
        help_text=_(
            'Final grade given to activity considering all responses, '
            'penalties, etc.'),
        max_digits=6,
        decimal_places=3,
        blank=True,
        null=True,
    )

    @classmethod
    def get_response(cls, user, activity, context=None):
        """
        Return the response object associated with the given
        user/activity/context.

        Create a new response object if it does not exist.
        """

        if user is None or activity is None:
            raise TypeError(
                'Response objects must be bound to an user or activity.'
            )

        response, create = Response.objects.get_or_create(
            user=user, activity=activity, context=context
        )
        return response

    def grade(self, method=None, force_update=False):
        """
        Return the final grade for the user using the given method.

        If not method is given, it uses the default grading method for the
        activity.
        """

        activity = self.activity

        # Choose grading method
        if method is None and self.final_grade is not None:
            return self.final_grade
        elif method is None:
            grading_method = activity.grading_method
        else:
            grading_method = GradingMethod.from_name(activity.owner, method)

        # Grade response. We save the result to the final_grade attribute if
        # no explicit grading method is given.
        grade = grading_method.grade(self)
        if method is None and (force_update or self.final_grade is None):
            self.final_grade = grade
        return grade
