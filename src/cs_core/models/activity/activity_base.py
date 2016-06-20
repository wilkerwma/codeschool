import decimal
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist
from codeschool import models
from codeschool import blocks
from codeschool import panels
import cs_core.blocks
from . import GradingMethod

ZERO = decimal.Decimal(0)
RESOURCE_BLOCKS = [
    ('paragraph', blocks.RichTextBlock()),
    ('image', blocks.ImageChooserBlock()),
    # ('embed', blocks.EmbedBlock()),
    # ('markdown', blocks.MarkdownBlock()),
    # ('url', blocks.URLBlock()),
    # ('text', blocks.TextBlock()),
    # ('char', blocks.CharBlock()),
    # ('ace', blocks.AceBlock()),
    # ('bool', blocks.BooleanBlock()),
    # ('doc', blocks.DocumentChooserBlock()),
    # ('snippet', blocks.SnippetChooserBlock(GradingMethod)),
    # ('date', blocks.DateBlock()),
    # ('time', blocks.TimeBlock()),
    # ('stream', blocks.StreamBlock([
    #     ('page', blocks.PageChooserBlock()),
    #     ('html', blocks.RawHTMLBlock())
    # ])),
]


def grading_method_best():
    """
    Return the "best" GradingMethod instance.
    """

    from cs_core.models import GradingMethod
    return GradingMethod.best().pk


class ActivityQueryset(models.PageQuerySet):
    def auth(self, user, role=None):
        """
        Filter only activities that the user can see.
        """

        # Filter by course
        courses = Course.objects.auth(user, role)
        course_ids = courses.values_list('id', flat=True)
        qs = self.filter(course__in=course_ids)

        # Filter by explicit student association
        return qs.distinct()


class ActivityMeta(type(models.Page)):
    """
    Metaclass for both Polymorphic and wagtail's Page.
    """


class Activity(models.CopyMixin,
               # models.PolymorphicModel,  # make polymorphic_ctype configurable
               models.ShortDescribablePage,
               metaclass=ActivityMeta):
    """
    Represents a gradable activity inside a course. Activities may not have an
    explicit grade, but yet may provide points to the students via the
    gamefication features of Codeschool.

    Activities can be scheduled to be done in the class or as a homework
    assignment.

    Each concrete activity is represented by a different subclass.
    """

    class Meta:
        abstract = True
        verbose_name = _('activity')
        verbose_name_plural = _('activities')

    grading_method = models.ForeignKey(
        GradingMethod,
        on_delete=models.SET_DEFAULT,
        default=grading_method_best,
        blank=True,
        help_text=_('Choose the strategy for grading this activity.')
    )
    icon_src = models.CharField(
        _('activity icon'),
        max_length=50,
        blank=True,
        help_text=_(
            'Optional icon name that can be used to personalize the activity. '
            'Material icons are available by using the "material:" namespace '
            'as in "material:menu".'),
    )
    resources = models.StreamField(RESOURCE_BLOCKS)
    objects = models.PageManager.from_queryset(ActivityQueryset)()

    @property
    def course(self):
        """
        Points to the course object or None if owner is not a course.
        """

        return getattr(self.get_parent(), 'course_instance', None)

    @course.setter
    def course(self, value):
        self.set_parent(value)

    #: Define the default material icon used in conjunction with instances of
    #: the activity class.
    default_material_icon = 'help'

    #: The response class associated with the given activity.
    response_class = None

    @property
    def material_icon(self):
        """
        The material icon used in conjunction with the activity.
        """

        if self.icon_src.startswith('material:'):
            return self.icon_src[9:]
        return self.default_material_icon

    @property
    def icon_html(self):
        """
        A string of HTML source that points to the icon element fo the activity.
        """

        return '<i class="material-icon">%s</i>' % self.material_icon

    def __init__(self, *args, **kwargs):
        # Get parent page from initialization
        course = kwargs.pop('course', None)
        discipline = kwargs.pop('discipline', None)
        user = kwargs.pop('user', None)
        if sum(1 for x in [course, discipline, user] if x is not None) >= 2:
            raise TypeError(
                'Can only use one of course, discipline or user arguments.'
            )
        super().__init__(*args, **kwargs)
        parent = course or discipline or user
        if parent is not None:
            self.set_parent(parent)

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

    # Wagtail admin
    subpage_types = []
    parent_page_types = [
        'cs_core.Course',
        'cs_core.LessonPage'
    ]
    content_panels = models.CodeschoolPage.content_panels + [
        panels.MultiFieldPanel([
            panels.RichTextFieldPanel('short_description'),
            panels.FieldPanel('grading_method'),
        ], heading=_('Options')),
    ]
    promote_panels = models.CodeschoolPage.promote_panels + [
        panels.FieldPanel('icon_src')
    ]
    settings_panels = models.CodeschoolPage.settings_panels + [
        panels.StreamFieldPanel('resources'),
    ]
