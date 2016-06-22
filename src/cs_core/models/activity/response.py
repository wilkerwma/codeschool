import decimal
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from codeschool import models
from codeschool import blocks


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

    __updated = False

    context = models.ForeignKey(
        'cs_core.ResponseContext',
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
        default=0,
    )

    @property
    def num_attempts(self):
        """
        The number of attempts made to solve the question.
        """
        return self.items.count()

    @classmethod
    def from_db(cls, *args, **kwargs):
        obj = super().from_db(*args, **kwargs)
        obj.activity = obj.activity.specific
        obj.update()
        return obj

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

    def __str__(self):
        tries = self.num_attempts
        user = self.user
        activity = self.activity
        grade = '%s pts' % (self.final_grade or 0)
        fmt = '<Response: %s by %s (%s, %s tries)>'
        return fmt % (activity, user, grade, tries)

    def update(self, force=False):
        """
        Synchronize object so its state accounts for the latest responses.
        """
        if not self.__updated or self.final_grade is None or force:
            # We check if any response_item was updated after the main response
            # object. If so, we recompute the grades using the maximum grade
            # criterium
            # TODO: in the future we should use grading_mehod
            changed_items = self.items.filter(modified__gte=self.modified)
            if changed_items or True:
                grades = self.items.values_list('final_grade', flat=True)
                self.final_grade = max(grades, default=self.final_grade or 0)
                self.save(update_fields=['final_grade'])
            elif self.final_grade is None:
                self.final_grade = 0.0
                self.save(update_fields=['final_grade'])
            self.__updated = True

    def clean(self):
        if not isinstance(self.activity, Activity):
            raise ValidationError({'activity': _('Not an activity.')})
        if self.context is None:
            self.context = getattr(self.activity, 'default_context')

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
