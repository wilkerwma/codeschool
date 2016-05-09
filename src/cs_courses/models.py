from django.utils import timezone
from django.core.urlresolvers import reverse as url_reverse
from django.utils.translation import ugettext_lazy as _
from autoslug import AutoSlugField
from wagtail.wagtailcore.fields import RichTextField
from codeschool import models
from cs_activities.models import Activity
from cs_auth.models import FriendshipStatus as FriendShip

#
# Main model classes
#
class Faculty(models.Model):
    """Describes a faculty/department or any institution that is responsible for
     some given discipline"""

    name = models.CharField(_('name'), max_length=200)
    description = RichTextField(_('description'), blank=True)


class Discipline(models.Model):
    """A discipline represents one abstract academic discipline.

    Each discipline can be associated with many courses."""

    name = models.CharField(_('name'), max_length=200)
    abbreviation = AutoSlugField(populate_from='name')
    short_description = models.TextField(_('short description'))
    long_description = RichTextField(_('long description'))

    def __str__(self):
        return '%s (%s)' % (self.name, self.abbreviation)


class Course(models.DateFramedModel, models.TimeStampedModel):
    """One specific occurrence of a course for a given teacher in a given
    period."""

    # Fields
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

    def save(self, *args, **kwds):
        super().save(*args,**kwds)
        for student in self.students.values():
            for colleague in self.students.values():
                if(student["id"] != colleague["id"]):
                    obj_student = models.User(**student)
                    obj_colleague = models.User(**colleague)
                    try:
                       FriendShip.objects.get(owner=obj_student,
                                              other=obj_colleague) 
                    except FriendShip.DoesNotExist:
                        FriendShip(owner=obj_student,
                                   other=obj_colleague,
                                   status="colleague").save()
                                
        
    # Managers
    @property
    def past_activities(self):
        return (
            self.activities.filter(status=Activity.STATUS.concluded) |
            self.activities.filter(end__lt=timezone.now())
        ).select_subclasses()

    @property
    def open_activities(self):
        return (self.activities.timeframed.all() &
                self.activities.filter(status=Activity.STATUS.open)).select_subclasses()

    @property
    def pending_activities(self):
        return (self.activities.filter(status=Activity.STATUS.draft) |
                (self.activities.filter(status=Activity.STATUS.open) &
                 self.activities.filter(end__lt=timezone.now()))).select_subclasses()

    # Use information from discipline
    name = property(lambda s: s.discipline.name)
    short_description = property(lambda s: s.discipline.short_description)
    long_description = property(lambda s: s.discipline.long_description)

    def __str__(self):
        return '%s (%s)' % (self.discipline.name, self.teacher.first_name)

    def get_absolute_url(self):
        return url_reverse('course-detail', args=(self.pk,))

    def role(self, user):
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

    def user_activities(self, user):
        """Return a list of all activities that are valid for the given user"""

        return self.activities.select_subclasses()

    def activity_duration(self):
        """Return the default duration for an activity starting from now."""

        return 120

    def next_time_slot(self):
        """Return the start and end times for the next class in the course.

        If a time slot is currently open, return it."""

        now = timezone.now()
        return now, now + timezone.timedelta(self.activity_duration())

    def next_date(self, date=None):
        """Return the date of the next available time slot."""


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
Course.lessons = Lesson.get_descriptor()
models.User.related_courses = property(
        lambda self:
            (self.enrolled_courses.all() |
             self.owned_courses.all() |
             self.courses_as_staff.all()).distinct()
)
