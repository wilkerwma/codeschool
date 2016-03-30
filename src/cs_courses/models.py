from django.utils import timezone
from django.core.urlresolvers import reverse as url_reverse
from autoslug import AutoSlugField
from wagtail.wagtailcore.fields import RichTextField
from codeschool import models
from cs_activities.models import Activity


#
# Main model classes
#
class Faculty(models.Model):
    """Describes a faculty/department or any institution that is responsible for
     some given discipline"""

    name = models.CharField(max_length=200)
    description = RichTextField(blank=True)


class Discipline(models.Model):
    """A discipline represents one abstract academic discipline.

    Each discipline can be associated with many courses."""

    # Basic info
    name = models.CharField(max_length=200)
    abbreviation = AutoSlugField(populate_from='name')
    short_description = models.TextField()
    long_description = RichTextField()

    # Meta-info
    # internal_id = models.CharField(max_length=100, blank=True)
    # faculty = models.ForeignKey(Faculty, null=True, blank=True)

    # Other info
    # bibliography = models.ManyToManyField(Publication)
    # syllabus = models.RichTextField()
    # program = models.RichTextField()

    def __str__(self):
        return '%s (%s)' % (self.name, self.abbreviation)


class FixableModel(models.Model):
    class Meta:
        abstract = True

    def save(self, *args, fix_state=True, **kwds):
        # Options: force_insert=False, force_update=False, using=None,
        # update_fields=None,
        if fix_state:
            fields = self.fix_state()
            if fields is None:
                self.save(fix_state=False)
            elif fields:
                self.save(update_fields=fields, fix_state=False)
        super().save(*args, **kwds)

    @classmethod
    def from_db(cls, db, field_names, values, *, fix_state=True):
        obj = super().from_db(db, field_names, values)
        if fix_state:
            fields = obj.fix_state()
            if fields is None:
                obj.save(fix_state=False)
            elif fields:
                obj.save(update_fields=fields, fix_state=False)
        return obj

    def fix_state(self):
        """Called before saving or loading object from db.

        This function should return a list of updated fields or None in order
        to update all fields. If not field requires update, the return list
        should be empty."""

        return []


class Course(models.TimeFramedModel, models.TimeStampedModel, FixableModel):
    """One specific ocurrence of a course for a given teacher in a given
    period."""

    # Basic info
    discipline = models.ForeignKey(Discipline, related_name='courses')
    teacher = models.ForeignKey(models.User, related_name='owned_courses')
    students = models.ManyToManyField(
        models.User,
        related_name='enrolled_courses',
        blank=True,
    )
    current_lesson = models.ForeignKey(
        'Lesson',
        blank=True, null=True,
        related_name='course_as_current'
    )
    is_active = models.BooleanField(default=False)

    # Override discipline info
    long_description_override = RichTextField(
            'Descrição detalhada',
            blank=True,
            help_text='Descrição longa e detalhada do curso',
    )
    short_description_override = models.TextField(
            'Descrição curta',
            blank=True,
            help_text='Descrição curta que funciona como um "tweet" para '
                      'descrever o curso. Ex.: "Apenda os fundamentos de '
                      'programação"'
    )

    # Delegate properties
    @property
    def long_description(self):
        return (self.long_description_override or
                self.discipline.long_description)

    @property
    def short_description(self):
        return (self.short_description_override or
                self.discipline.short_description)

    @property
    def name(self):
        return self.discipline.name

    # Custom loading and saving
    def fix_state(self):
        fields = []
        rogue_lessons = self.lessons.filter(index__lt=0)
        if self.current_lesson is None and rogue_lessons:
            self.current_lesson = rogue_lessons.order_by('pk').first()
            self.current_lesson.index = 0
            self.current_lesson.save(update_fields=['index'])
            fields.append('current_lesson')
        elif rogue_lessons:
            good_lessons = self.lessons.filter(index__gte=0).order_by('index')
            last = good_lessons.last()
            last_idx = last.index
            for lesson in rogue_lessons.order_by('pk'):
                last_idx += 1
                lesson.index = last_idx
                lesson.save(update_fields=['index'])
        return fields

    # Magic methods
    def __str__(self):
        return '%s (%s)' % (self.discipline.name, self.teacher.first_name)

    def get_absolute_url(self):
        return url_reverse('course-detail', args=(self.pk,))

    def get_user_activities(self, user):
        """Return a list of all activities for the given user"""

        result = []
        activities = self.activities.filter(end__gt=timezone.now())
        for activity in activities.select_subclasses():
            if activity.group is None:
                result.append(activity)
            elif user in activities.group.users:
                result.append(activity)

        # Return a QuerySet?
        return result

    def get_past_activities(self):
        return (
            self.activities.filter(status=Activity.STATUS.concluded) |
            self.activities.filter(end__lt=timezone.now())
        ).select_subclasses()

    def get_open_activities(self):
        return (self.activities.timeframed.all() &
                self.activities.filter(status=Activity.STATUS.open)).select_subclasses()

    def get_pending_activities(self):
        return (self.activities.filter(status=Activity.STATUS.draft) |
                (self.activities.filter(status=Activity.STATUS.open) &
                 self.activities.filter(end__lt=timezone.now()))).select_subclasses()

    def default_duration(self):
        """Return the default duration for an activity starting from now."""

        return 120

    def next_class(self):
        """Return the start and end times for the next class in the course.

        If a time slot is open for right now, return the current slot."""

        now = timezone.now()
        return now, now + timezone.timedelta(self.default_duration())


#
# Accessory models
#
class TimeSlot(models.Model):
    """Represents the weekly time slot that can be assigned to classes for a
    given course."""

    weekday = models.IntegerField(
        choices=[(0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'),
                 (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'),
                 (6, 'Sunday')]
    )
    start = models.TimeField()
    end = models.TimeField()
    course = models.ForeignKey(Course)
    room = models.CharField(max_length=100, blank=True)


class Lesson(models.Model):
    """A single lesson in a doubly linked list."""

    index = models.IntegerField()
    real_date = models.DateField(null=True, blank=True)
    scheduled_date = models.DateField(null=True, blank=True)
    title = models.CharField(max_length=140, blank=True)
    description = models.TextField(blank=True)
    course = models.ForeignKey(Course, related_name='lessons')

    def save(self, *args, **kwds):
        if self.index is None:
            if self.course.lessons:
                last = self.course.lessons.order_by('index').last()
                self.index = last.index + 1
            else:
                self.index = 0
        super().save(*args, **kwds)


    #class Meta:
    #    unique_together = ('index', 'course')

    def next(self, skip=1):
        if self.index >= 0:
            try:
                return self.course.lessons.get(index=self.index + skip)
            except self.DoesNotExist:
                return None
        else:
            raise ValueError('cannot iterate over rogue lessons')

    def prev(self, skip=1):
        return self.next(-skip)

    def __str__(self):
        return self.description

