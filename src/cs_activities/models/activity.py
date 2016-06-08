import decimal
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist
from model_utils.managers import InheritanceQuerySet
from codeschool import models
from cs_activities.models import GradingMethod

ZERO = decimal.Decimal(0)
ACTIVITY_OWNER_CONTENT_CHOICES = (
    models.Q(app_label='cs_courses', model='course') |
    models.Q(app_label='django.contrib.auth', model='user')
)


def grading_method_best():
    """
    Return the "best" GradingMethod instance.
    """

    return GradingMethod.best().pk


class ActivityQueryset(InheritanceQuerySet):
    def auth(self, user, role=None):
        """
        Filter only activities that the user can see.
        """

        # Filter by course
        courses = Course.objects.auth(user, role)
        course_ids = courses.values_list('id', flat=True)
        qs = self.filter(course__in=courses)

        # Filter by explicit student association
        return qs.distinct()


class Activity(models.CopyMixin,
               models.InheritableModel,
               models.DescribableModel,
               models.TimeFramedModel):
    """
    Represents a gradable activity inside a course. Activities may not have an
    explicit grade, but yet may provide points to the students via the
    gamefication features of Codeschool.

    Activities can be scheduled to be done in the class or as a homework
    assignment.

    Each concrete activity is represented by a different subclass.
    """

    class Meta:
        verbose_name = _('activity')
        verbose_name_plural = _('activities')

    STATUS_OPEN = 'open'
    STATUS_CLOSED = 'closed'
    STATUS_VISIBLE = 'visible'
    STATUS_DRAFT = 'draft'
    STATUS_EXPIRED = 'expired',
    STATUS = models.Choices(
        (STATUS_DRAFT, _('draft')),
        (STATUS_OPEN, _('open')),
        (STATUS_CLOSED, _('closed')),
        (STATUS_VISIBLE, _('visible')),
        (STATUS_EXPIRED, _('expired')),
    )
    status = models.StatusField(
        _('status'),
        help_text=_(
            'Only open activities will be visible and active to all students.'),
    )
    published_at = models.MonitorField(
        _('date of publication'),
        monitor='status',
        when=['open']
    )
    icon_src = models.CharField(
        max_length=50,
        blank=True,
        help_text=_(
            'Optional icon name that can be used to personalize the activity. '
            'Material icons are available by using the "material:" namespace '
            'as in "material:menu".'),
    )
    owner_content_type = models.ForeignKey(
        ContentType,
        verbose_name=_('owner model type'),
        limit_choices_to=ACTIVITY_OWNER_CONTENT_CHOICES,
        related_name='activities_as_owner',
        null=True,
        blank=True,
    )
    owner_id = models.PositiveIntegerField(
        _("owner model's id"),
        null=True,
        blank=True,
    )
    target_content_type = models.ForeignKey(
        ContentType,
        verbose_name=_('target model type'),
        related_name='activities_as_target',
        null=True,
        blank=True,
    )
    target_id = models.PositiveIntegerField(
        _("target model's id"),
        null=True,
        blank=True,
    )
    course = models.ForeignKey(
        'cs_courses.Course',
        related_name='activities',
        blank=True,
        null=True,
    )
    parent = models.ForeignKey(
        'self',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='children'
    )
    grading_method = models.ForeignKey(
        GradingMethod,
        default=grading_method_best,
        blank=True,
    )

    #: The owner object is either a course object or an user object. This
    #: object has control to the given activity and define which users have
    #: permissions to access and edit it.
    owner_object = GenericForeignKey('owner_content_type', 'owner_id')

    #: The owner object is either a course object or an user object. This
    #: object has control to the given activity and define which users have
    #: permissions to access and edit it.
    target_object = GenericForeignKey('target_content_type', 'target_id')

    objects = ActivityQueryset.as_manager()

    @property
    def course_(self):
        """Points to the course object or None if owner is not a course."""

        obj = self.owner_object
        return obj if isinstance(obj, Course) else None

    @property
    def owner(self):
        """Points to the user that owns the activity."""

        obj = self.owner_object
        if isinstance(obj, models.User):
            return obj
        else:
            return self.course.owner

    #: Define the default material icon used in conjunction with instances of
    #: the activity class.
    default_material_icon = 'help'

    #: The response class associated with the given activity.
    response_class = None

    @property
    def material_icon(self):
        """The material icon used in conjunction with the activity."""

        if self.icon_src.startswith('material:'):
            return self.icon_src[9:]
        return self.default_material_icon

    @property
    def icon_html(self):
        """A string of HTML source that points to the icon element fo the
        activity."""

        return '<i class="material-icon">%s</i>' % self.material_icon

    # Permission control
    def can_edit(self, user):
        """
        Return True if user has permissions to edit activity.
        """

        return user == self.owner or self.course.can_edit(user)

    def can_view(self, user):
        """
        Return True if user has permission to view activity.
        """

        course = self.course
        return (
            self.can_edit(user) or
            user in course.students.all() or
            user in self.staff.all()
        )

    # Other functions
    def get_absolute_url(self):
        return reverse('activity:detail', kwargs={'pk': self.pk})

    # Response and grading control
    def has_user_response(self, user):
        """
        Return True if the user has responsed to the question.

        Use either :func:`Activity.get_user_response` or
        :func:`Activity.get_user_responses` methods to fetch the user responses.
        """

        return bool(self.responses.filter(user=user))

    def get_user_response(self, user, method='first'):
        """
        Return some response given by the user or None if the user has not
        responded.

        Allowed methods:
            unique:
                Expects that response is unique and return it (or None).
            any:
                Return a random user response.
            first:
                Return the first response given by the user.
            last:
                Return the last response given by the user.
            best:
                Return the response with the best final grade.
            worst:
                Return the response with the worst final grade.
            best-given:
                Return the response with the best given grade.
            worst-given:
                Return the response with the worst given grade.

        """

        responses = self.responses.filter(user=user)
        first = lambda x: x.select_subclasses().first()

        if method == 'unique':
            N = self.responses.count()
            if N == 0:
                return None
            elif N == 1:
                return response.select_subclasses().first()
            else:
                raise ValueError(
                    'more than one response found for user %r' % user.username
                )
        elif method == 'any':
            return first(responses)
        elif method == 'first':
            return first(responses.order_by('created'))
        elif method == 'last':
            return first(responses.order_by('-created'))
        elif method in ['best', 'worst', 'best-given', 'worst-given']:
            raise NotImplementedError(
                'method = %r is not implemented yet' % method
            )
        else:
            raise ValueError('invalid method: %r' % method)

    def get_user_responses(self, user):
        """
        Return all responses by the given user.
        """

        return self.responses.filter(user=user).select_subclasses()

    def get_user_final_response(self, user):
        """Return the FinalResponse object associated with the given user."""

        try:
            return self.final_responses.get(user=user)
        except ObjectDoesNotExist:
            return self.final_responses.create(user=user)

    def get_user_grade(self, user):
        """
        Return the numeric grade associated with the user.
        """

        final_response = self.get_user_final_response(user)
        return final_response.grade()

    def select_responses(self):
        """
        Return a queryset with all responses related to the given question.
        """
        from cs_activities.models import Response

        if not force:
            responses = self.responses.filter(status=Response.STATUS_PENDING)
        else:
            responses = self.responses.all()
        return responses.select_subclasses()

    def grade_responses(self, force=False):
        """
        Grade all responses that had not been graded yet.

        This function may take a while to run, locking the server. Maybe it is
        a good idea to run it as a task or in a separate thread.

        Args:
            force (boolean):
                If True, forces the response to be re-graded.
        """

        # Run autograde on each responses
        for response in responses:
            response.autograde(force=force)

    def select_users(self):
        """
        Return a queryset with all users that responded to the activity.
        """

        user_ids = self.responses.values_list('user', flat=True).distinct()
        users = models.User.objects.filter(id__in=user_ids)
        return users

    def get_grades(self, users=None):
        """
        Return a dictionary mapping each user to their respective grade in the
        activity.

        If a list of users is given, include only the users in this list.
        """

        if users is None:
            users = self.select_users()

        grades = {}
        for user in users:
            grade = self.get_user_grade(user)
            grades[user] = grade
        return grades
