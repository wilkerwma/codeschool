from django.utils.translation import ugettext_lazy as _, ugettext as __
from django.apps import apps
from wagtail.wagtailcore.models import PageQuerySet, PageManager, Page
from codeschool import models
from codeschool import panels
from codeschool.utils import delegate_to


class CourseQueryset(PageQuerySet):
    def auth(self, user, role=None):
        """
        Filter to only courses that the given user can see.

        An optional role can be added so only courses in which the user is
        related with the specific role are considered. Valid roles are
        'teacher', 'student' or 'staff'.
        """

        qs = self.none()

        if role is None or role in ['student', 'can_view']:
            qs |= user.courses_as_students.all()
        if role is None or role in ['staff', 'can_view']:
            qs |= user.courses_as_staff.all()
        if role is None or role in ['teacher', 'can_edit']:
            qs |= user.courses_as_teacher.all()
        return qs.distinct()


class Course(models.RoutablePageMixin, models.CodeschoolPage):
    """
    One specific occurrence of a course for a given teacher in a given period.
    """

    class Meta:
        parent_init_attribute = 'discipline'

    teachers = models.ManyToManyField(
        models.User,
        related_name='courses_as_teacher',
        blank=True,
    )
    students = models.ManyToManyField(
        models.User,
        related_name='courses_as_student',
        blank=True,
    )
    staff = models.ManyToManyField(
        models.User,
        related_name='courses_as_staff_p',
        blank=True,
    )
    weekly_lessons = models.BooleanField(
        _('weekly lessons'),
        default=False,
        help_text=_(
            'If true, the lesson spans a whole week. Othewise, each lesson '
            'would correspond to a single day/time slot.'
        ),
    )
    accept_subscriptions = models.BooleanField(
        _('accept subscriptions'),
        default=True,
        help_text=_(
            'Set it to false to prevent new student subscriptions.'
        ),
    )
    is_public = models.BooleanField(
        _('is it public?'),
        default=False,
        help_text=_(
            'If true, all students will be able to see the contents of the '
            'course. Most activities will not be available to non-subscribed '
            'students.'
        ),
    )
    subscription_passphrase = models.CharField(
        _('subscription passphrase'),
        max_length=140,
        help_text=_(
            'A passphrase/word that students must enter to subscribe in the '
            'course. Leave empty if no passphrase should be necessary.'
        ),
        blank=True,
    )
    objects = PageManager.from_queryset(CourseQueryset)()

    short_description = delegate_to('discipline', True)
    long_description = delegate_to('discipline', True)
    short_description_html = delegate_to('discipline', True)
    long_description_html = delegate_to('discipline', True)
    lessons = property(lambda x: x.calendar_page.lessons)

    @property
    def calendar_page(self):
        content_type = models.ContentType.objects.get(
            app_label='cs_core',
            model='calendarpage'
        )
        return apps.get_model('cs_core', 'CalendarPage').objects.get(
            depth=self.depth + 1,
            path__startswith=self.path,
            content_type_id=content_type,
        )

    @property
    def questions_page(self):
        content_type = models.ContentType.objects.get(
            app_label='cs_questions',
            model='questionlist'
        )
        return apps.get_model('cs_questions', 'QuestionList').objects.get(
            depth=self.depth + 1,
            path__startswith=self.path,
            content_type_id=content_type,
        )

    @property
    def gradables_page(self):
        content_type = models.ContentType.objects.get(
            app_label='cs_core',
            model='gradablespage'
        )
        return apps.get_model('cs_core', 'GradablesPage').objects.get(
            depth=self.depth + 1,
            path__startswith=self.path,
            content_type_id=content_type,
        )

    @property
    def discipline(self):
        return self.get_parent().specific

    @discipline.setter
    def discipline(self, value):
        self.set_parent(value)

    @property
    def questions(self):
        return self.questions_page.questions

    def add_question(self, question, copy=True):
        """
        Register a new question to the course.

        If `copy=True` (default), register a copy.
        """

        self.questions.add_question(question, copy)

    def new_question(self, cls, *args, **kwargs):
        """
        Create a new question instance by calling the cls with the given
        arguments and add it to the course.
        """

        self.questions.new_question(cls, *args, **kwargs)

    def add_lesson(self, lesson, copy=True):
        """
        Register a new lesson in the course.

        If `copy=True` (default), register a copy.
        """

        self.lessons.add_lesson(lesson, copy)

    def new_lesson(self, *args, **kwargs):
        """
        Create a new lesson instance by calling the Lesson constructor with the
        given arguments and add it to the course.
        """

        self.lessons.new_lesson(*args, **kwargs)

    def register_student(self, student):
        """
        Register a new student in the course.
        """

        self.students.add(student)
        self.update_friendship_status(student)

    def update_friendship_status(self, student=None):
        """
        Recompute the friendship status for a single student by marking it as
        a colleague of all participants in the course..

        If no student is given, update the status of all enrolled students.
        """

        update = self._update_friendship_status
        if student is None:
            for student in self.students.all():
                update(student)
        else:
            update(student)

    def _update_friendship_status(self, student):
        # Worker function for update_friendship_status
        colleague_status = FriendshipStatus.STATUS_COLLEAGUE
        for colleague in self.students.all():
            if colleague != student:
                try:
                    FriendshipStatus.objects.get(owner=student,
                                                 other=colleague)
                except FriendshipStatus.DoesNotExist:
                    FriendshipStatus.objects.create(owner=student,
                                                    other=colleague,
                                                    status=colleague_status)

    def get_absolute_url(self):
        return url_reverse('course-detail', args=(self.pk,))

    def get_user_role(self, user):
        """Return a string describing the most privileged role the user
        as in the course. The possible values are:

        teacher:
            Owns the course and can do any kind of administrative tasks in
            the course.
        staff:
            Teacher assistants. May have some privileges granted by the teacher.
        student:
            Enrolled students.
        visitor:
            Have no relation to the course. If course is marked as public,
            visitors can access the course contents.
        """

        if user == self.teacher:
            return 'teacher'
        if user in self.staff.all():
            return 'staff'
        if user in self.students.all():
            return 'student'
        return 'visitor'

    def get_user_activities(self, user):
        """
        Return a sequence of all activities that are still open for the user.
        """

        activities = self.activities.filter(status=Activity.STATUS_OPEN)
        return activities.select_subclasses()

    def activity_duration(self):
        """
        Return the default duration (in minutes) for an activity starting from
        now.
        """

        return 120

    def next_time_slot(self):
        """Return the start and end times for the next class in the course.

        If a time slot is currently open, return it."""

        now = timezone.now()
        return now, now + timezone.timedelta(self.activity_duration())

    def next_date(self, date=None):
        """Return the date of the next available time slot."""

    def can_view(self, user):
        return user != annonymous_user()

    def can_edit(self, user):
        return user in self.teachers.all() or user == self.owner

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context['activities'] = self.questions
        return context

    # Wagtail admin
    parent_page_types = ['cs_core.Discipline']
    subpage_types = []
    content_panels = Page.content_panels + [
        panels.InlinePanel(
            'time_slots',
            label=_('Time slots'),
            help_text=_('Define when the weekly classes take place.'),
        ),
    ]
    settings_panels = Page.settings_panels + [
        panels.MultiFieldPanel([
            panels.FieldPanel('weekly_lessons'),
            panels.FieldPanel('is_public'),
        ], heading=_('Options')),
        panels.MultiFieldPanel([
            panels.FieldPanel('accept_subscriptions'),
            panels.FieldPanel('subscription_passphrase'),
        ], heading=_('Subscription')),

    ]


class TimeSlot(models.Model):
    """
    Represents the weekly time slot that can be assigned to lessons for a
    given course.
    """

    class Meta:
        ordering = ('weekday', 'start')

    MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY = range(7)
    WEEKDAY_CHOICES = [
        (MONDAY, _('Monday')),
        (TUESDAY, _('Tuesday')),
        (WEDNESDAY, _('Wednesday')),
        (THURSDAY, _('Thursday')),
        (FRIDAY, _('Friday')),
        (SATURDAY, _('Saturday')),
        (SUNDAY, _('Sunday'))
    ]
    course = models.ParentalKey(
        'Course',
        related_name='time_slots'
    )
    weekday = models.IntegerField(
        _('weekday'),
        choices=WEEKDAY_CHOICES,
        help_text=_('Day of the week in which this class takes place.')
    )
    start = models.TimeField(
        _('start'),
        blank=True,
        null=True,
        help_text=_('The time in which the class starts.'),
    )
    end = models.TimeField(
        _('ends'),
        blank=True,
        null=True,
        help_text=_('The time in which the class ends.'),
    )
    room = models.CharField(
        _('classroom'),
        max_length=100,
        blank=True,
        help_text=_('Name for the room in which this class takes place.'),
    )

    # Wagtail admin
    panels = [
        panels.FieldRowPanel([
            panels.FieldPanel('weekday', classname='col6'),
            panels.FieldPanel('room', classname='col6'),
        ]),
        panels.FieldRowPanel([
            panels.FieldPanel('start', classname='col6'),
            panels.FieldPanel('end', classname='col6'),
        ]),
    ]

# Patch user model
models.User.related_courses = property(
    lambda self: Course.objects.auth(self)
)
