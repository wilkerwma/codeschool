import decimal
import json
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import ugettext_lazy as _
from django.core.signals import Signal
from codeschool.jinja.filters import markdown
from codeschool import models
from codeschool.utils import md5hash
from cs_core.models.activity import Response


#: This signal is emitted when a response item finishes its autograde() method
#: successfully and sets the ResponseItem status to STATUS_DONE.
autograde_signal = Signal(providing_args=['response_item', 'given_grade'])


class ResponseItem(models.CopyMixin,
                   models.TimeStampedStatusModel,
                   models.PolymorphicModel):
    """
    Represents a student's response to some activity.

    Response objects have 4 different states:

    pending:
        The response has been sent, but was not graded. Grading can be manual or
        automatic, depending on the activity.
    waiting:
        Waiting for manual feedback.
    incomplete:
        For long-term activities, this tells that the student started a response
        and is completing it gradually, but the final response was not achieved
        yet.
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
    STATUS_INCOMPLETE = 'incomplete'
    STATUS_WAITING = 'waiting'
    STATUS_INVALID = 'invalid'
    STATUS_DONE = 'done'
    STATUS = models.Choices(
        (STATUS_PENDING, _('pending')),
        (STATUS_INCOMPLETE, _('incomplete')),
        (STATUS_WAITING, _('waiting')),
        (STATUS_INVALID, _('invalid')),
        (STATUS_DONE, _('done')),
    )

    response = models.ParentalKey(
        'Response',
        verbose_name=_('response'),
        related_name='items',
    )
    feedback_data = models.JSONField(
        null=True,
        blank=True,
    )
    response_data = models.JSONField(
        null=True,
        blank=True,
    )
    response_hash = models.CharField(
        max_length=32,
        blank=True,
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

    # Status properties
    is_done = property(lambda x: x.status == x.STATUS_DONE)
    is_pending = property(lambda x: x.status == x.STATUS_PENDING)
    is_waiting = property(lambda x: x.status == x.STATUS_WAITING)
    is_invalid = property(lambda x: x.status == x.STATUS_INVALID)

    # Delegate properties
    activity = property(lambda x: x.response.activity.specific)
    user = property(lambda x: x.response.user)
    context = property(lambda x: x.response.context)
    course = property(lambda x: x.activity.course)

    def __init__(self, *args, **kwargs):
        # Django is loading object from the database -- we step out the way
        if args and not kwargs:
            super().__init__(*args, **kwargs)
            return

        # We create the response_data and feedback_data manually always using
        # copies of passed dicts. We save these variables here, init object and
        # then copy this data to the initialized dictionaries
        response_data = kwargs.pop('response_data', None) or {}
        feedback_data = kwargs.pop('feedback_data', None) or {}

        # This part makes a ResponseItem instance initialize from a user +
        # activity + context instead of requiring a response object. The
        # response is automatically created on demand.
        user = kwargs.pop('user', None)
        if user:
            context = kwargs.pop('context', None)
            try:
                activity = kwargs.pop('activity')
            except KeyError:
                raise TypeError(
                    'ReponseItem objects bound to a user must also provide an '
                    'activity parameter.'
                )

            # User-bound constructor tries to obtain the Response object by
            # searching for an specific (user, context, activity) tuple.
            response, created = Response.objects.get_or_create(
                user=user,
                context=context,
                activity=activity
            )
            kwargs['response'] = response

        if 'context' in kwargs or 'activity' in kwargs:
            raise TypeError(
                'Must provide an user to instantiate a bound response item.'
            )
        super().__init__(*args, **kwargs)

        # Now that we have initialized the response item, we fill the data
        # passed in the response_data and feedback_data dictionaries.
        self.response_data = dict(self.response_data or {}, **response_data)
        self.feedback_data = dict(self.response_data or {}, **feedback_data)

    def __str__(self):
        if self.given_grade is None:
            grade = self.status
        else:
            grade = '%s pts' % self.final_grade
        user = self.user
        activity = self.activity
        return '<ResponseItem: %s by %s (%s)>' % (activity, user, grade)

    def save(self, *args, **kwargs):
        if not self.response_hash:
            self.response_hash = self.get_response_hash(self.response_hash)
        super().save(*args, **kwargs)

    def get_feedback_data(self, commit=True):
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

    def autograde(self, commit=True, force=False, silent=False):
        """
        Performs automatic grading.

        Response subclasses must implement the autograde_compute() method in
        order to make automatic grading work. This method may write any
        relevant information to the `feedback_data` attribute and must return
        a numeric value from 0 to 100 with the given automatic grade.

        Args:
            commit:
                If false, prevents saving the object when grading is complete.
                The user must save the object manually after calling this
                method.
            force:
                If true, force regrading the item even if it has already been
                graded.
            silent:
                Prevents the autograde_signal from triggering in the end of
                a successful autograde.
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
                if self.final_grade is None:
                    self.final_grade = self.given_grade
                self.status = self.STATUS_DONE
                if not silent:
                    autograde_signal.send_robust(
                        self.__class__,
                        response_item=self,
                        given_grade=self.given_grade
                    )
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

    def regrade(self, method, commit=True):
        """
        Recompute the grade for the given response item.

        If status != 'done', it simply calls the .autograde() method. Otherwise,
        it accept different strategies for updating to the new grades:
            'update':
                Recompute the grades and replace the old values with the new
                ones. Only saves the response item if the feedback_data or the
                given_grade attributes change.
            'best':
                Only update if the if the grade increase.
            'worst':
                Only update if the grades decrease.
            'best-feedback':
                Like 'best', but updates feedback_data even if the grades
                change.
            'worst-feedback':
                Like 'worst', but updates feedback_data even if the grades
                change.

        Return a boolean telling if the regrading was necessary.
        """
        if self.status != self.STATUS_DONE:
            return self.autograde()

        # We keep a copy of the state, if necessary. We only have to take some
        # action if the state changes.
        def rollback():
            self.__dict__.clear()
            self.__dict__.update(state)

        state = self.__dict__.copy()
        self.autograde(force=True, commit=False)

        # Each method deals with the new state in a different manner
        if method == 'update':
            if state != self.__dict__:
                if commit:
                    self.save()
                return False
            return True
        elif method in ('best', 'best-feedback'):
            if self.given_grade <= state.get('given_grade', 0):
                new_feedback_data = self.feedback_data
                rollback()
                if new_feedback_data != self.feedback_data:
                    self.feedback_data = new_feedback_data
                    if commit:
                        self.save()
                    return True
                return False
            elif commit:
                self.save()
            return True

        elif method in ('worst', 'worst-feedback'):
            if self.given_grade >= state.get('given_grade', 0):
                new_feedback_data = self.feedback_data
                rollback()
                if new_feedback_data != self.feedback_data:
                    self.feedback_data = new_feedback_data
                    if commit:
                        self.save()
                    return True
                return False
            elif commit:
                self.save()
            return True
        else:
            rollback()
            raise ValueError('invalid method: %s' % method)

    @classmethod
    def get_response_hash(cls, response_data):
        """
        Computes a hash for the response_data attribute.
        """

        if response_data:
            data = json.dumps(response_data, default=json_default)
            return md5hash(data)
        return ''

    # Feedback and visualization
    ok_message = _('*Congratulations!* Your response is correct!')
    ok_with_penalties = _('Your response is correct, but you did not achieved '
                          'the maximum grade.')
    wrong_message = _('I\'m sorry, your response is wrong.')
    partial_message = _('Your answer is partially correct: you achieved only '
                        '%(grade)d%% of the total grade.')

    def html_feedback(self):
        """
        A string of html source representing the feedback.
        """

        if self.is_done:
            data = {'grade': (self.final_grade or 0)}

            if self.final_grade == 100:
                return markdown(self.ok_message)
            elif self.given_grade == 100:
                return markdown(self.ok_with_penalties_message)
            elif not self.given_grade:
                return markdown(self.wrong_message)
            else:
                return markdown(self.partial_message % data)
        else:
            return markdown(_('Your response has not been graded yet!'))

    # Permissions
    def can_edit(self, user):
        return False

    def can_view(self, user):
        return user == self.user


class InvalidResponseError(Exception):
        """Raised by compute_response() when the response is invalid."""


# Save a copy in the class namespace for convenience
ResponseItem.InvalidResponseError = InvalidResponseError


# The default serializer for JSON data. We have to accept a few extra types
# when calculating the hash from a JSON dump.
from functools import singledispatch
from decimal import Decimal
#from datetime import date, time, datetime


@singledispatch
def json_default(x):
    raise TypeError


@json_default.register(Decimal)
def _(x):
    return str(x)

