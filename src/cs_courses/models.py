from django.utils import timezone
from django.core.urlresolvers import reverse as url_reverse
from django.utils.translation import ugettext_lazy as _
from autoslug import AutoSlugField
from codeschool import models
from cs_activities.models import Activity
from cs_auth.models import FriendshipStatus
from wagtail.wagtailcore.models import Page


#
# Main model classes
#
class FacultyPage(models.DescribableModel, Page):
    """Describes a faculty/department or any institution that is responsible for
     disciplines"""


class Discipline(models.DescribableModel):
    """A discipline represents one abstract academic discipline.

    Each discipline can be associated with many courses."""

    abbreviation = AutoSlugField(populate_from='name')

    def __str__(self):
        return '%s (%s)' % (self.name, self.abbreviation)


class CourseQueryset(models.QuerySet):
    def auth(self, user, role=None):
        """
        Filter to only courses that the given user can see.

        An optional role can be added so only courses in which the user is
        related with the specific role are considered. Valid roles are
        'teacher', 'student' or 'staff'.
        """

        qs = self.none()

        if role is None or role in ['student', 'can_view']:
            qs |= user.enrolled_courses.all()
        if role is None or role in ['staff', 'can_view']:
            qs |= user.courses_as_staff.all()
        if role is None or role in ['teacher', 'can_edit']:
            qs |= self.filter(teacher=user)
        return qs.distinct()


class Course(models.DateFramedModel, models.TimeStampedModel):
    """One specific occurrence of a course for a given teacher in a given
    period."""

    discipline = models.ForeignKey(
        Discipline,
        related_name='courses'
    )
    teacher = models.ForeignKey(
        models.User,
        related_name='owned_courses'
    )
    students = models.ManyToManyField(
        models.User,
        related_name='enrolled_courses',
        blank=True,
    )
    staff = models.ManyToManyField(
        models.User,
        related_name='courses_as_staff',
        blank=True,
    )
    current_lesson_index = models.PositiveIntegerField(default=0, blank=True)
    current_lesson_start = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(_('is active'), default=False)
    objects = CourseQueryset.as_manager()

    # Discipline properties
    name = property(lambda x: x.discipline.name)
    short_description = property(lambda x: x.discipline.short_description)
    long_description = property(lambda x: x.discipline.long_description)
    short_description_html = property(lambda x:
                                      x.discipline.short_description_html)
    long_description_html = property(lambda x:
                                     x.discipline.long_description_html)

    # Other properties
    owner = property(lambda x: x.teacher)

    def __str__(self):
        return '%s (%s)' % (self.discipline.name, self.teacher.first_name)

    def to_file(self):
        """Serialize object in a Markdown format."""

    @classmethod
    def from_file(self, file):
        """Load course from file."""

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

    # Managers
    @property
    def past_activities(self):
        return (
            self.activities.filter(status=Activity.STATUS_CLOSED) |
            self.activities.filter(end__lt=timezone.now())
        ).select_subclasses()

    @property
    def open_activities(self):
        return (
            self.activities.timeframed.all() &
            self.activities.filter(status=Activity.STATUS_OPEN)
        ).select_subclasses()

    @property
    def pending_activities(self):
        return (
            self.activities.filter(status=Activity.STATUS_DRAFT) |
            (self.activities.filter(status=Activity.STATUS_OPEN) &
             self.activities.filter(end__lt=timezone.now()))
        ).select_subclasses()

    def get_absolute_url(self):
        return url_reverse('course-detail', args=(self.pk,))

    def get_user_role(self, user):
        """Return a string describing the most priviledged role the user
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
        return True

    def can_edit(self, user):
        return user == self.teacher


class TimeSlot(models.Model):
    """Represents the weekly time slot that can be assigned to classes for a
    given course."""

    class Meta:
        unique_together = ('course', 'weekday')

    weekday = models.IntegerField(
        choices=[(0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'),
                 (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'),
                 (6, 'Sunday')]
    )
    start = models.TimeField()
    end = models.TimeField()
    course = models.ForeignKey(Course)
    room = models.CharField(max_length=100, blank=True)


class Lesson(models.ListItemModel):
    """A single lesson in a doubly linked list."""

    class Meta:
        verbose_name = _('Lesson')
        verbose_name_plural = _('Lessons')
        root_field = 'course'

    title = models.CharField(max_length=140, blank=True)
    description = models.TextField(blank=True)
    date = models.DateField(null=True, blank=True)
    course = models.ForeignKey(Course)

    def __str__(self):
        return self.title


# Patch models
Course.lessons = Lesson.as_items()
models.User.related_courses = property(
        lambda self:
            (self.enrolled_courses.all() |
             self.owned_courses.all() |
             self.courses_as_staff.all()).distinct()
)
