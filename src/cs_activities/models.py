from codeschool import models
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from codeschool.jinja.filters import markdown


class Activity(models.InheritableModel):
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
        blank=True, null=True,
        related_name='children'
    )

    _default_material_icon = 'help_underline'

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
        return reverse('activity', args=(self.pk,))

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


class Response(models.InheritableModel, models.TimeStampedStatusModel):
    """
    Represents a student's response to some activity. The student may submit
    many responses for the same object. It is also possible to submit
    different responses with different students.
    """

    STATUS_PENDING = 'pending'
    STATUS_WAITING = 'waiting'
    STATUS_INVALID = 'invalid'
    STATUS_DONE = 'done'
    STATUS = models.Choices(
        (STATUS_PENDING, _('pending')),
        (STATUS_WAITING, _('waiting')),
        (STATUS_DONE, _('done')),
    )
    activity = models.ForeignKey(Activity, blank=True, null=True)
    user = models.ForeignKey(models.User)
    grade = models.DecimalField(
        'Percentage of maximum grade',
        max_digits=6,
        decimal_places=3,
        blank=True,
        null=True,
    )
    data = models.PickledObjectField(blank=True, null=True)

    #
    # Visualization
    #
    ok_message = '*Contratulations!* Your response is correct!'
    wrong_message = 'I\'m sorry, your response is wrong.'
    partial_message = 'Your answer is partially correct: you made %(grade)d%% of the total grade.'

    def as_html(self):
        data = {'grade': self.grade * 100}
        if self.grade == 1:
            return markdown(self.ok_message)
        elif self.grade == 0:
            return markdown(self.wrong_message)
        else:
            return markdown(self.partial_message % data)

    def __str__(self):
        tname = type(self).__name__
        return '%s(%s, grade=%s)' % (tname, self.activity, self.grade)
