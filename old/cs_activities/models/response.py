import decimal
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import ugettext_lazy as _
from codeschool import models
from codeschool.jinja.filters import markdown
from cs_activities.models import GradingMethod, Activity


class Response(models.CopyMixin,
               models.InheritableModel,
               models.TimeStampedStatusModel):
    """
    Represents a student's response to some activity.

    Response objects have 4 different states:

    pending:
        The response has been sent, but was not graded. Grading can be manual or
        automatic, depending on the activity.
    waiting:
        Waiting for manual feedback.
    invalid:
        The response has been sent, but contains malformed data.
    done:
        The response was graded and evaluated and it initialized a feedback
        object.

    A response always starts at pending status. We can request it to be graded
    by calling the :func:`Response.autograde` method. This method must raise
    an InvalidResponseError if the response is invalid or ManualGradingError if
    the response subclass does not implement automatic grading.
    """

    class Meta:
        verbose_name = _('response')
        verbose_name_plural = _('responses')

    STATUS_PENDING = 'pending'
    STATUS_WAITING = 'waiting'
    STATUS_INVALID = 'invalid'
    STATUS_DONE = 'done'
    STATUS = models.Choices(
        (STATUS_PENDING, _('pending')),
        (STATUS_WAITING, _('waiting')),
        (STATUS_INVALID, _('invalid')),
        (STATUS_DONE, _('done')),
    )
    activity = models.ForeignKey(
        Activity,
        blank=True,
        null=True,
        related_name='responses',
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        models.User,
        blank=True,
        null=True,
    )
    feedback_data = models.PickledObjectField(
        blank=True,
        null=True
    )
    given_grade = models.DecimalField(
        _('Percentage of maximum grade'),
        help_text=_(
            'This grade is given by the auto-grader and represents the grade '
            'for the response before accounting for any bonuses or penalties.'),
        max_digits=6,
        decimal_places=3,
        blank=True,
        null=True,
    )
    final_grade = models.DecimalField(
        _('Final grade'),
        help_text=_(
            'Similar to given_grade, but can account for additional factors '
            'such as delay penalties or for any other reason the teacher may '
            'want to override the student\'s grade.'),
        max_digits=6,
        decimal_places=3,
        blank=True,
        null=True,
    )
    manual_override = models.BooleanField(
        default=False
    )
    parent = models.ForeignKey(
        'self',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='children',
    )
    is_converted = models.BooleanField(default=False)

    # Status properties
    is_done = property(lambda x: x.status == x.STATUS_DONE)
    is_pending = property(lambda x: x.status == x.STATUS_PENDING)
    is_waiting = property(lambda x: x.status == x.STATUS_WAITING)
    is_invalid = property(lambda x: x.status == x.STATUS_INVALID)

    # Delegate properties
    course = property(lambda x: getattr(x.activity, 'course', None))

    # Other properties
    @property
    def grade(self):
        if self.final_grade is None:
            return self.given_grade or decimal.Decimal(0)
        else:
            return self.final_grade
    grade.setter(lambda x, v: setattr(x, 'final_grade', v))

    class InvalidResponseError(Exception):
        """Raised by compute_response() when the response is invalid."""

    # Compute grades
    def get_response_group(self, user):
        """Return the response group associated to this response."""

    def get_feedback(self, commit=True):
        """Return the feedback object associated to the given response.

        This method may trigger the autograde() method, if grading was not
        performed yet. If you want to defer database access, call it with
        commit=False to prevent saving any modifications to the response object
        to the database.
        """

        if self.status == self.STATUS_PENDING:
            self.autograde(commit)
        elif self.status == self.STATUS_INVALID:
            raise self.feedback_data
        elif self.status == self.STATUS_WAITING:
            return None
        return self.feedback_data

    def autograde(self, commit=True, force=False):
        """
        Performs automatic grading.

        Response subclasses must implement the autograde_compute() method in
        order to make automatic grading work. This method may write any
        relevant information to the `feedback_data` attribute and must return
        a numeric value from 0 to 100 with the given automatic grade.
        """

        if self.status == self.STATUS_PENDING or force:
            try:
                value = self.autograde_compute()
            except self.InvalidResponseError as ex:
                self.status = self.STATUS_INVALID
                self.feedback_data = ex
                self.given_grade = self.final_grade = decimal.Decimal(0)
                if commit:
                    self.save()
                raise

            if value is None:
                self.status = self.STATUS_WAITING
            else:
                self.given_grade = decimal.Decimal(value)
                self.final_grade = self.given_grade
                self.status = self.STATUS_DONE
            if commit and self.pk:
                self.save(update_fields=['status', 'feedback_data',
                                         'given_grade', 'final_grade'])
            elif commit:
                self.save()

        elif self.status == self.STATUS_INVALID:
            raise self.feedback_data

    def autograde_compute(self):
        """This method should be implemented in subclasses."""

        raise ImproperlyConfigured(
            'Response subclass %r must implement the autograde_compute().'
            'This method should perform the automatic grading and return the '
            'resulting grade. Any additional relevant feedback data might be '
            'saved to the `feedback_data` attribute, which is then is pickled '
            'and saved into the database.' % type(self).__name__
        )

    def __str__(self):
        return '%s(%s)' % (type(self).__name__, self.status)

    # Feedback and visualization
    ok_message = _('*Congratulations!* Your response is correct!')
    wrong_message = _('I\'m sorry, your response is wrong.')
    partial_message = _('Your answer is partially correct: you achieved only '
                        '%(grade)d%% of the total grade.')

    def html_feedback(self):
        """
        A string of html source representing the feedback.
        """

        if self.is_done:
            data = {'grade': (self.grade or 0)}

            if self.grade == 100:
                return markdown(self.ok_message)
            elif not self.grade:
                return markdown(self.wrong_message)
            else:
                return markdown(aself.partial_message % data)
        else:
            return markdown(_('Your response has not been graded yet!'))

    # Permissions
    def can_edit(self, user):
        return False

    def can_view(self, user):
        return user == self.user


class FinalResponse(models.CopyMixin, models.Model):
    """
    Gather all responses of the same user to a given activity together.

    This is useful in grading when e.g., selecting for the average/best/worst/
    first/last grade.
    """

    class Meta:
        unique_together = [('user', 'activity')]
        verbose_name = _('final response')
        verbose_name_plural = _('final responses')

    user = models.ForeignKey(
        models.User,
        related_name='final_responses',
    )
    activity = models.ForeignKey(
        Activity,
        blank=True,
        null=True,
        related_name='final_responses',
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

    def get_responses(self):
        """
        Return a queryset with all responses associated with the user.
        """

        return self.activity.get_user_responses(self.user)

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

    def __iter__(self):
        return iter(self.get_responses())

    def __len__(self):
        return self.get_responses().count()
