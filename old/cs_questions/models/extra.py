from django.utils.translation import ugettext_lazy as _
from codeschool import models
from cs_questions.models.base import (Question, QuestionActivity,
                                      QuestionResponse)


class FreeAnswerQuestion(Question):
    """
    Question expects a free text answer that must be manually graded.
    """
    DATA_FILE = 'file'
    DATA_IMAGE = 'image'
    DATA_PDF = 'pdf'
    DATA_PLAIN = 'plain'
    DATA_RICHTEXT = 'richtext'
    DATA_CHOICES = (
        (DATA_FILE, _('Arbitrary file')),
        (DATA_IMAGE, _('Image file')),
        (DATA_PDF, _('PDF file')),
        (DATA_RICHTEXT, _('Rich text input')),
        (DATA_RICHTEXT, _('Plain text input')),
    )
    metadata = models.TextField()
    data_type = models.CharField(choices=DATA_CHOICES, max_length=10)
    data_file = models.FileField(blank=True, null=True)


class FileFreeAnswerQuestion(Question):
    """
    Question expects a file answer that must be manually graded.
    """


class BooleanQuestion(Question):
    """
    A question with a single boolean answer.
    """

    answer_key = models.BooleanField()


class StringMatchQuestion(Question):
    """
    The student response is compared with an answer_key string either by
    simple string comparison or using a regular expression.
    """

    answer_key = models.TextField()
    is_regex = models.BooleanField(default=True)

    def grade(self, response):
        if self.is_regex:
            value = response.value

        else:
            return super().grade(response)
