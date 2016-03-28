import datetime
from codeschool import models
from django.utils.translation import ugettext_lazy as _


class Activity(models.InheritableModel, models.TimeFramedStatusModel):
    """Represents a gradable activity inside a course. It can be scheduled to
    be done in class or as a homework assignment.

    Each concrete activity is represented by a different subclass.
    """
    STATUS = models.Choices('open', 'draft', 'concluded')

    course = models.ForeignKey('cs_courses.Course', related_name='activities')
    group = models.ForeignKey(
            models.Group,
            verbose_name=_('Group of students'),
            help_text=_('Group of students that this activity is assigned to. '
                        'Leave blank to assign to the whole classroom.'),
            null=True,
            blank=True,
    )
    max_grade = models.FloatField(default=0, blank=True)

    class Meta:
        verbose_name = _('Activity')
        verbose_name_plural = _('Activities')

    @property
    def students(self):
        if self.student_group is None:
            return self.course.students
        else:
            return self.student_group.students

    # TODO: remove this? Rendering functions
    def as_card(self):
        return '''
        <div class="card">
            <i class="material-icons">work</i>
            <h1>Atividade</h1>
            <p>%s</p>
        </div>
        ''' % self.short_description

    def as_html(self):
        return '''
        <div class="card">
            <i class="material-icons">work</i>
            <h1>Atividade</h1>
            <p>%s</p>
        </div>
        ''' % self.description


class GenericActivity(Activity):
    name = models.CharField(max_length=200)
    short_description = models.CharField(max_length=140)
    long_description = models.TextField()


#
# Responses
#
class Response(models.InheritableModel, models.TimeStampedStatusModel):
    """
    Represents a student's response to some question. The student may submit
    many responses for the same object. It is also possible to submit
    different responses with different students.
    """

    STATUS = models.Choices('pending', 'graded')

    activity = models.ForeignKey(Activity)
    group = models.ForeignKey(models.Group)


class TextualResponse(Response):
    """Responses represented as a single string of text"""

    text = models.TextField()


class Feedback(models.InheritableModel, models.TimeStampedModel):

    response = models.ForeignKey(Response)
    grade = models.DecimalField(
        'Percentage of maximum grade',
        max_digits=6,
        decimal_places=2,
        blank=True,
        null=True,
    )
