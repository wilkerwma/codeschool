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


class Course(models.TimeFramedModel, models.TimeStampedModel):
    """One specific ocurrence of a course for a given teacher in a given
    period."""

    # Basic info
    discipline = models.ForeignKey(Discipline, related_name='courses')
    teacher = models.ForeignKey(models.User, related_name='owned_courses')
    students = models.ManyToManyField(models.User, related_name='enrolled_courses')
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
    given course"""

    weekday = models.IntegerField()
    start = models.TimeField()
    end = models.TimeField()
    course = models.ForeignKey(Course)
