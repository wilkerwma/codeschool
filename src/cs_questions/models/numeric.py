from django.utils.translation import ugettext_lazy as _
from codeschool import models
from cs_questions.models.base import (Question, QuestionActivity,
                                      QuestionResponse)


class NumericResponse(QuestionResponse):
    """The response object to a simple numeric question."""

    value = models.FloatField(
        _('Value'),
        help_text=_('Result (it must be a number)')
    )

    def autograde_compute(self):
        question = self.question
        if abs(self.value - question.answer) <= question.tolerance:
            return 100
        else:
            return 0


class NumericQuestion(Question):
    """A simple numeric question.

    Student must tell a numeric value within a tolerance margin."""

    answer = models.FloatField(
        _('Answer'),
        help_text=_('The numeric value for the correct answer')
    )
    tolerance = models.FloatField(
        _('Tolerance'),
        help_text=_('If given, defines the tolerance within responses are '
                    'still considered to be correct'),
        default=0,
        blank=True,
    )

    response_cls = NumericResponse

    @property
    def is_exact(self):
        return self.tolerance == 0

    @property
    def start(self):
        return self.answer - abs(self.tolerance)

    @property
    def end(self):
        return self.answer + abs(self.tolerance)

    @property
    def range(self):
        return self.start, self.end

    def grade(self, response):
        x, y = self.range
        response.grade = (100 if x <= response.value <= y else 0)
        response.save()
