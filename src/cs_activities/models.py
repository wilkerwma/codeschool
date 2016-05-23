import decimal
from django.core.exceptions import ObjectDoesNotExist, ImproperlyConfigured
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from codeschool import models
from codeschool.jinja.filters import markdown


class Activity(models.CopyMixin, models.InheritableModel):
    """Represents a gradable activity inside a course. It can be scheduled to
    be done in class or as a homework assignment.

    Each concrete activity is represented by a different subclass.
    """
    STATUS_OPEN = 'open'
    STATUS_CLOSED = 'closed'
    STATUS_VISIBLE = 'visible'
    STATUS_DRAFT = 'draft'
    STATUS = models.Choices(
        (STATUS_DRAFT, _('draft')),
        (STATUS_OPEN, _('open')),
        (STATUS_CLOSED, _('closed')),
        (STATUS_VISIBLE, _('visible')),
    )
    status = models.StatusField(
        _('status'),
        help_text=_('Only open activities will be visible and active to all '
                    'students.'),
    )
    published_at = models.MonitorField(
        _('date of publication'),
        monitor='status',
        when=['open']
    )
    icon_src = models.CharField(max_length=50, blank=True)
    name = models.CharField(max_length=200)
    short_description = models.CharField(max_length=140, blank=True)
    long_description = models.TextField(blank=True)
    course = models.ForeignKey('cs_courses.Course', related_name='activities')
    parent = models.ForeignKey(
        'self',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='children'
    )
    allow_multiple_responses = models.BooleanField(default=True)

    _default_material_icon = 'help'

    @property
    def material_icon(self):
        if self.icon_src.startswith('material:'):
            return self.icon_src[9:]
        return self._default_material_icon

    class Meta:
        verbose_name = _('activity')
        verbose_name_plural = _('activities')

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('activity:detail', kwargs={'pk': self.pk})

    def can_edit(self, user):
        """Return True if user has permissions to edit activity."""

        return user == self.course.teacher

    def can_view(self, user):
        """Return True if user has permission to view activity."""

        return (
            user == self.course.teacher or
            user in self.course.staff.all() or
            user in self.course.students.all()
        )

    # Permissions
    def can_edit(self, user):
        return self.course.teacher == user

    def can_view(self, user):
        course = self.course
        return (
            self.can_edit(user) or
            user in course.students.all() or
            user in self.staff.all()
        )


class SyncCodeActivity(Activity):
    """
    In this activity, the students follow a piece of code that someone
    edits and is automatically updated in all of student machines. It keeps
    track of all modifications that were saved by the teacher.
    """

    _default_material_icon = 'code'
    language = models.ForeignKey('cs_core.ProgrammingLanguage')

    @property
    def last(self):
        try:
            return self.data.order_by('timestamp').last()
        except SyncCodeEditItem.DoesNotExist:
            return None

    @property
    def first(self):
        try:
            return self.data.order_by('timestamp').first()
        except SyncCodeEditItem.DoesNotExist:
            return None


class SyncCodeEditItem(models.Model):
    """
    A simple state of the code in a SyncCodeActivity.
    """

    activity = models.ForeignKey(SyncCodeActivity, related_name='data')
    text = models.TextField()
    next = models.OneToOneField('self', blank=True, null=True,
                                related_name='previous')
    timestamp = models.DateTimeField(auto_now=True)

    @property
    def prev(self):
        try:
            return self.previous
        except ObjectDoesNotExist:
            return None


class ResponseGroup(models.CopyMixin, models.Model):
    """Gather a group of responses of the same user together.

    This is useful to
    """
    user = models.ForeignKey(models.User)
    activity = models.ForeignKey(Activity)

    def grade_last_response(self, user):
        """Return the last last response submited by the user."""

    def grade_best_response(self, user):
        """Return the response with the best grade."""


class Response(models.CopyMixin,
               models.InheritableModel,
               models.TimeStampedStatusModel):
    """
    Represents a student's response to some activity.

    Response objects can be in 4 different states:

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
    activity = models.ForeignKey(Activity, blank=True, null=True,
                                 related_name='responses')
    user = models.ForeignKey(models.User)
    feedback_data = models.PickledObjectField(blank=True, null=True)
    given_grade = models.DecimalField(
        _('Percentage of maximum grade'),
        help_text=_('This grade is given by the auto-grader and represents'
                    'the grade for the response before accounting for any '
                    'bonuses or penalties.'),
        max_digits=6,
        decimal_places=3,
        blank=True,
        null=True,
    )
    final_grade = models.DecimalField(
        _('Final grade'),
        help_text=_('Similar to given_grade, but can account for additional '
                    'factors such as delay penalties or any reason the teacher '
                    'may want to override the student\'s grade.'),
        max_digits=6,
        decimal_places=3,
        blank=True,
        null=True,
    )
    manual_override = models.BooleanField(default=False)
    parent = models.ForeignKey(
        'self',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='children',
    )

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

    def autograde(self, commit=True):
        """Performs auto grading."""

        if self.status == self.STATUS_PENDING:
            try:
                self._autograde_helper()
            except self.InvalidResponseError as ex:
                self.status = self.STATUS_INVALID
                self.feedback_data = ex
                self.given_grade = self.final_grade = decimal.Decimal(0)
                if commit:
                    self.save()
                raise
            else:
                if self.feedback_data is None:
                    self.status = self.STATUS_WAITING
                else:
                    grade = decimal.Decimal(self.get_grade_from_feedback())
                    self.final_grade = self.given_grade = grade
                    self.status = self.STATUS_DONE
            if commit and self.pk:
                self.save(update_fields=['status', 'feedback_data',
                                         'given_grade', 'final_grade'])
            elif commit:
                self.save()
        elif self.status == self.STATUS_INVALID:
            raise self.feedback_data

    def _autograde_helper(self):
        """This method should be implemented in subclasses."""

        raise ImproperlyConfigured(
            'Response subclasses must implement the _autograde_helper() method '
            'and save all relevant feedback data in the `feedback_data` '
            'attribute. This value is pickled and saved to the database.'
        )

    def get_grade_from_feedback(self):
        """Return the grade from the feedback_data attribute."""

        raise ImproperlyConfigured(
            'Response subclasses must implement the get_grade_from_feedback() '
            'method that computes the grade from the feedback_data object. The'
            'return value should be a decimal.Decimal() value in the 0-100 '
            'range.'
        )

    def __str__(self):
        tname = type(self).__name__
        return '%s(%s)' % (tname, self.status)

    # Feedback and visualization
    ok_message = _('*Contratulations!* Your response is correct!')
    wrong_message = _('I\'m sorry, your response is wrong.')
    partial_message = _('Your answer is partially correct: you made %(grade)d%% of the total grade.')

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
