from iospec import parse_string as parse_iospec
from iospec import feedback as iofeedback
import ejudge
import ejudge.contrib.pytuga
from django.db import models
from model_utils.managers import InheritanceManager
from picklefield import PickledObjectField
from wagtail.wagtailcore.fields import RichTextField
from codeschool.shortcuts import lazy, delegation
from codeschool import constants
from cs_courses import models as courses_models
from cs_activities.models import Activity, Feedback


#
# Base Question class
#
class Question(models.Model):
    """Base class for all question types"""

    title = models.CharField(max_length=200)
    short_description = models.CharField(max_length=140)
    long_description = RichTextField()
    author_name = models.CharField('Author', max_length=100, blank=True)
    comment = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    question_type = models.IntegerField(null=True)
    discipline = models.ForeignKey(courses_models.Discipline, blank=True, null=True)

    objects = InheritanceManager()

    class Meta:
        permissions = (("download_question", "Can download question files"),)

    def __str__(self):
        return self.title


#
# Basic question types: question_type starts at 10 up to 99
#
class FreeAnswerQuestion(Question):
    pass


class NumericQuestion(Question):
    answer_start = models.FloatField()
    answer_end = models.FloatField(blank=True, null=True)
    is_exact = models.BooleanField(default=True)


class BooleanQuestion(Question):
    answer_key = models.BooleanField()


class StringMatchQuestion(Question):
    template = models.TextField()
    is_regex = models.BooleanField(default=True)


#
# Programming related questions: question_types starts at 100 up to 999
#
class CodeIoQuestion(Question):
    """CodeIo questions evaluates code and judge them by their inputs and
    outputs."""

    iospec_expanded = models.TextField(blank=True)
    iospec = models.TextField(
            'Response template',
            blank=True,
            help_text='Template used to grade I/O responses. See http://??? for'
                      'a complete reference on the template format.',
    )
    timeout = models.FloatField(
            'Timeout',
            default=1.0,
            help_text='Timeout in seconds',
    )
    grader = PickledObjectField(null=True)

    class Meta:
        verbose_name = 'I/O coding question'
        verbose_name_plural = 'I/O coding questions'

    @lazy
    def iospec_tree(self):
        return parse_iospec(self.iospec)

    @lazy
    def expanded_tree(self):
        if self.iospec_expanded:
            return parse_iospec(self.iospec_expanded)
        else:
            tree = self.expand_iospec()
            self.iospec_expanded = tree.source()
            self.save(update_fields=['iospec_expanded'])
            return tree

    def expand_iospec(self):
        """Return a copy of iospec_tree with all computed inputs expanded and
        all input only nodes computed from an answer key."""

        tree = self.iospec_tree.copy()
        tree.expand_inputs()
        result = None

        for key in self.answer_keys.all():
            lang = key.language
            run = ejudge.io.run(key.source_code, tree, lang=lang)
            if result is None or run == result:
                result = run
            else:
                raise RuntimeError('Answer key for %s is giving different '
                                   'answers' % lang)
        return result


class CodeIoAnswerKey(models.Model):
    """Represents an answer to some question given in some specific computer
    language plus the placeholder text that should be displayed"""

    question = models.ForeignKey(CodeIoQuestion, related_name='answer_keys')
    language = models.CharField(
            'Programming language',
            max_length=10,
            choices=constants.language_choices)
    source_code = models.TextField(
            'Answer source code',
            default='',
            help_text='Source code for the correct answer in the given '
                      'programming language',
    )
    placeholder = models.TextField(
            'Placeholder code',
            blank=True,
            help_text='This optional field controls which code should be '
                      'placed in the source code editor when a question is '
                      'opened. This is useful to put boilerplate or even a '
                      'full program that the student should modify. It is '
                      'possible to configure a global per-language boilerplate '
                      'and leave this field blank.',
    )

    class Meta:
        verbose_name = 'Answer key'
        verbose_name_plural = 'Answer keys'

    def __str__(self):
        return self.language

    def grade(self, response):
        print('GRADING QUESTION')
        lang = self.language
        tree = self.question.expanded_tree
        source = response.text
        feedback = ejudge.io.grade(source, tree, lang=lang)
        print(feedback.case.source())
        print(feedback.answer_key.source())
        return CodeIoFeedback.from_feedback(feedback, response)


@delegation('question', ['long_description', 'short_description'])
class QuestionActivity(Activity):
    question = models.ForeignKey(Question)

    @property
    def name(self):
        return self.question.title


class CodeIoActivity(QuestionActivity):
    answer_key = models.ForeignKey(CodeIoAnswerKey)


class CodeIoFeedback(Feedback):
    case = models.TextField()
    answer_key = models.TextField()
    status = models.CharField(max_length=20)
    hint = models.TextField(blank=True)
    message = models.TextField(blank=True)

    @classmethod
    def from_feedback(cls, feedback, response):
        case = feedback.case
        answer_key = feedback.answer_key

        return CodeIoFeedback(
            response=response,
            grade=feedback.grade,
            case=case.source(),
            answer_key=answer_key.source(),
            status=feedback.status or '',
            hint=feedback.hint or '',
            message=feedback.message or '',
        )

    @lazy
    def _feedback(self):
        case = parse_iospec(self.case)
        answer_key = parse_iospec(self.answer_key)
        return iofeedback.Feedback(
            case, answer_key,
            status=self.status, hint=self.hint, message=self.message
        )

    @property
    def title(self):
        return self._feedback.title

    def as_html(self, *args, **kwds):
        return self._feedback.as_html(*args, **kwds)

    def as_text(self, *args, **kwds):
        return self._feedback.as_text(*args, **kwds)