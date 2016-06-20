import decimal
from django.apps import apps
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
    ('embed', blocks.EmbedBlock()),
    ('markdown', blocks.MarkdownBlock()),
    ('url', blocks.URLBlock()),
    ('text', blocks.TextBlock()),
    ('char', blocks.CharBlock()),
    ('ace', blocks.AceBlock()),
    ('bool', blocks.BooleanBlock()),
    ('doc', blocks.DocumentChooserBlock()),
    ('snippet', blocks.SnippetChooserBlock(GradingMethod)),
    ('date', blocks.DateBlock()),
    ('time', blocks.TimeBlock()),
    ('stream', blocks.StreamBlock([
        ('page', blocks.PageChooserBlock()),
        ('html', blocks.RawHTMLBlock())
    ])),
]


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


# noinspection SpellCheckingInspection,PyPep8Naming
class bound_property(property):
    """
    Just like a property, but tells the .bind() function of a question to
    handle it as a bound property.
    """


class Activity(models.CopyMixin,
               models.ShortDescribablePage):
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

    # --------------------------------------------------------------------------
    # References
    @property
    def course(self):
        """
        Points to the course this activity belongs to.
        """

        return getattr(self.get_parent(), 'course_instance', None)

    @course.setter
    def course(self, value):
        self.set_parent(value)

    @property
    def default_context(self):
        """
        Return the default context.
        """

        cls = apps.get_model('cs_core', 'ResponseContext')
        return cls.objects.get_or_create(activity_id=self.id,
                                         name='default')[0]

    # --------------------------------------------------------------------------
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

    # --------------------------------------------------------------------------
    # We define the optional user and context objects to bind responses to the
    # question object. These are not saved into the database, but are rather
    # used as default values to fill-in in the response objects. These objects
    # can be bound at init time or using the bind() method.
    @bound_property
    def user(self):
        return getattr(self, '_user', None)

    @user.setter
    def user(self, value):
        if isinstance(value, int):
            value = models.User.objects.get(pk=value)
        elif isinstance(value, str):
            value = models.User.objects.get(username=value)
        if not isinstance(value, (models.User, type(None))):
            raise TypeError('invalid user: %r' % value)
        self._user = value

    @bound_property
    def response_context(self):
        try:
            return self._context
        except AttributeError:
            return self.default_context

    @response_context.setter
    def context(self, value):
        if isinstance(value, int):
            value = ResponseContext.objects.get(pk=int)
        if not isinstance(value, (models.ResponseContext, type(None))):
            raise TypeError('invalid context: %r' % value)
        self._context = value

    # Bound tests
    @property
    def is_user_bound(self):
        return self.user is not None

    @property
    def is_context_bound(self):
        return self.context is not None

    # --------------------------------------------------------------------------
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

    def bind(self, *args, **kwargs):
        """
        Temporary binds objects to activity.

        This is useful to bind a question instance to some specific user or
        response context. These changes are not persisted on the database and
        are just a convenience for using other methods.

        This method accept a single positional argument for passing a request
        object. Any number of keyword arguments might be given for each
        registered binding properties for the object. For convenience, invalid
        arguments are just ignored.
        """

        if args:
            request = args[0]
            kwargs.setdefault('user', request.user)

        # We check in the class if each item is a bound_property. If so, we
        # save its value with the given data.
        cls = self.__class__
        for k, v in kwargs.items():
            if isinstance(getattr(cls, k, None), bound_property):
                setattr(self, k, v)

        # Return self so this method can be chained.
        return self

    # --------------------------------------------------------------------------
    # Response control
    def get_response(self, user=None, context=None):
        """
        Get the response associated with given user and context.

        If no user and context is given, use the bound values.
        """

        user = user or self.user
        context = context or self.context
        Response = apps.get_model('cs_core', 'Response')
        return Response.get_response(user=user, context=context, activity=self)

    def register_response_item(self, *,
                               user=None,
                               context=None,
                               autograde=False,
                               **kwargs):
        """
        Create a new response item object for the given question and saves it on
        the database.
        """
        user = user or self.user
        context = context or self.context
        response = self.response_item_class(
            user=user,
            context=context,
            activity=self,
            **kwargs,
        )
        if context.activity_id != self.id:
            context.activity.process_response_item(response)
        if autograde:
            response.autograde()
        else:
            response.save()
        return response

    def process_response_item(self, response):
        """
        Process this response item generated by other activities using a context
        that you own.

        This might happen in compound activities like quizzes, in which the
        response to a question uses a context own by a quiz object. This
        function allows the container object to take any additional action
        after the response is created.
        """

    def has_response(self, user=None, context=None):
        """
        Return True if the user has responded to the activity.
        """

        response = self.get_response(user, context)
        return response.response_items.count() >= 1

    # def get_user_response(self, user, method='first'):
    #     """
    #     Return some response given by the user or None if the user has not
    #     responded.
    #
    #     Allowed methods:
    #         unique:
    #             Expects that response is unique and return it (or None).
    #         any:
    #             Return a random user response.
    #         first:
    #             Return the first response given by the user.
    #         last:
    #             Return the last response given by the user.
    #         best:
    #             Return the response with the best final grade.
    #         worst:
    #             Return the response with the worst final grade.
    #         best-given:
    #             Return the response with the best given grade.
    #         worst-given:
    #             Return the response with the worst given grade.
    #
    #     """
    #
    #     responses = self.responses.filter(user=user)
    #     first = lambda x: x.select_subclasses().first()
    #
    #     if method == 'unique':
    #         N = self.responses.count()
    #         if N == 0:
    #             return None
    #         elif N == 1:
    #             return response.select_subclasses().first()
    #         else:
    #             raise ValueError(
    #                 'more than one response found for user %r' % user.username
    #             )
    #     elif method == 'any':
    #         return first(responses)
    #     elif method == 'first':
    #         return first(responses.order_by('created'))
    #     elif method == 'last':
    #         return first(responses.order_by('-created'))
    #     elif method in ['best', 'worst', 'best-given', 'worst-given']:
    #         raise NotImplementedError(
    #             'method = %r is not implemented yet' % method
    #         )
    #     else:
    #         raise ValueError('invalid method: %r' % method)
    #
    # def autograde_all(self, force=False, context=None):
    #     """
    #     Grade all responses that had not been graded yet.
    #
    #     This function may take a while to run, locking the server. Maybe it is
    #     a good idea to run it as a task or in a separate thread.
    #
    #     Args:
    #         force (boolean):
    #             If True, forces the response to be re-graded.
    #     """
    #
    #     # Run autograde on each responses
    #     for response in responses:
    #         response.autograde(force=force)
    #
    # def select_users(self):
    #     """
    #     Return a queryset with all users that responded to the activity.
    #     """
    #
    #     user_ids = self.responses.values_list('user', flat=True).distinct()
    #     users = models.User.objects.filter(id__in=user_ids)
    #     return users
    #
    # def get_grades(self, users=None):
    #     """
    #     Return a dictionary mapping each user to their respective grade in the
    #     activity.
    #
    #     If a list of users is given, include only the users in this list.
    #     """
    #
    #     if users is None:
    #         users = self.select_users()
    #
    #     grades = {}
    #     for user in users:
    #         grade = self.get_user_grade(user)
    #         grades[user] = grade
    #     return grades

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

    # Wagtail admin
    subpage_types = []
    parent_page_types = [
        'cs_core.Course',
        'cs_core.LessonPage'
    ]
    content_panels = models.CodeschoolPage.content_panels + [
        panels.MultiFieldPanel([
            panels.RichTextFieldPanel('short_description'),
        ], heading=_('Options')),
    ]
    promote_panels = models.CodeschoolPage.promote_panels + [
        panels.FieldPanel('icon_src')
    ]
    settings_panels = models.CodeschoolPage.settings_panels + [
        panels.StreamFieldPanel('resources'),
    ]
