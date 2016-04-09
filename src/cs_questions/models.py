import hashlib
from iospec import parse_string as parse_iospec
from iospec import feedback as iofeedback
import ejudge
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist
from model_utils.managers import InheritanceManager
from wagtail.wagtailcore.fields import RichTextField
from codeschool import constants
from codeschool import models
from codeschool.shortcuts import lazy, delegation, populate
from cs_courses import models as courses_models
from cs_activities.models import Activity, Feedback
from cs_core.models import ProgrammingLanguage


def md5hash(st):
    """Compute the hex-md5 hash of string.

    Returns a string of 32 ascii characters."""

    return hashlib.md5(st.encode('utf8')).hexdigest()


#
# Base Question class
#
class Question(models.TimeStampedModel):
    """Base class for all question types"""

    title = models.CharField(
        _('title'),
        max_length=200,
    )
    short_description = models.CharField(
        _('short description'),
        max_length=140,
        help_text=_('The short description is used in listings and should '
                    'present a brief one phrase description of the question.'),
    )
    long_description = RichTextField(
        _('long description'),
        help_text=_('The long and detailed description of the question that is'
                    'shown in the question submission form. This field '
                    'expects markdown markup.')
    )
    author_name = models.CharField(
        _('Author\'s name'),
        max_length=100,
        blank=True,
    )
    comment = models.TextField(
        _('Comments'),
        blank=True,
        help_text=_('The comments field is for any private information that '
                    'you should want to associate to the object. This field is '
                    'private and its contents are never revealed publicly.')
    )
    discipline = models.ForeignKey(
        courses_models.Discipline,
        blank=True,
        null=True,
        help_text=_('This optional field points to the discipline that is the '
                    'relevant to question.'),
    )
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

    iospec_size = models.PositiveIntegerField(
        _('number of iospec template expansions'),
        default=10,
        blank=True,
        help_text=_('The desired number of test cases that will be computed'
                    'after comparing the iospec template with the answer key.'
                    'This is only a suggested value and will only be applied if'
                    'the response template uses input commands to generate'
                    'random input.'),
    )
    iospec = models.TextField(
        _('response template'),
        blank=True,
        help_text=_('Template used to grade I/O responses. See '
                    'http://pythonhosted.org/iospec for a complete reference '
                    'on the template format.'),
    )
    timeout = models.FloatField(
            _('timeout in seconds'),
            default=5.0,
            help_text=_('Defines the maximum runtime the grader will spend '
                        'evaluating each test case.'),
    )

    class Meta:
        verbose_name = _('input/output question')
        verbose_name_plural = _('input/output questions')

    @lazy
    def iospec_tree(self):
        return parse_iospec(self.iospec)

    @lazy
    def expanded_tree(self):
        try:
            expansion = self.iospec_expansions.get(hash=md5hash(self.iospec))
            expansion.update_new_languages()
        except ObjectDoesNotExist:
            expansion = IoSpecExpansion.objects.create(
                question=self,
                hash=md5hash(self.iospec),
            )
            expansion.update_languages()
        return parse_iospec(expansion.source)

    def as_markio(self):
        """Render question as a Markio source"""

        import markio

        tree = markio.Markio(
            title=self.title,
            author=self.author_name,
            timeout=self.timeout,
            short_description=self.short_description,
            description=self.long_description,
            tests=self.iospec,
        )

        for key in self.answer_keys.all():
            tree.add_answer_key(key.source, key.ref)
            tree.add_placeholder(key.placeholder, key.ref)

        return tree.source()


class IoSpecExpansion(models.Model):
    """Represents a ready-to-use IoSpec expansion."""

    question = models.ForeignKey(
        CodeIoQuestion,
        related_name='iospec_expansions'
    )
    hash = models.CharField(max_length=32)
    needs_expansion = models.BooleanField(default=True)
    source = models.TextField(blank=True)
    validated_languages = models.ManyToManyField(
        ProgrammingLanguage,
        blank=True,
        related_name='valid_expansions'
    )
    invalid_languages = models.ManyToManyField(
        ProgrammingLanguage,
        blank=True,
        related_name='invalid_expansions'
    )

    @lazy
    def tree(self):
        if not self.needs_expansion:
            return parse_iospec(self.source)
        raise RuntimeError('cannot compute tree before expansion')

    @property
    def is_updated(self):
        return hash(self.question.iospec) == self.hash

    def get_languages(self):
        """Return a list of all languages that can be used to expand the input
        only blocks."""

        keys = self.question.answer_keys.exclude(source='')
        return [k.language for k in keys]

    def get_new_languages(self):
        """Return a list of all languages that can be used to expand the input
        only blocks that no computation were calculated."""

        return [lang for lang in self.get_languages()
                     if (lang not in self.validated_languages.all() and
                         lang not in self.invalid_languages.all())]

    def update_languages(self, langs=None):
        """Update all given languages.

        If not languages were given, update all available langauges."""

        if langs is None:
            langs = self.get_languages()

        # Return on empty list
        langs = list(langs)
        if not langs:
            return

        # Prepare to compute different runs
        basetree = self.question.iospec_tree
        if self.source:
            expanded = parse_iospec(self.source)
            expanded_lang = self.validated_languages.first()
        else:
            expanded = None
            expanded_lang = None

        for lang in langs:
            source = self.question.answer_keys.get(language=lang).source
            tree = basetree.copy()
            tree.expand_inputs(size=self.question.iospec_size)
            inputs = tree.inputs()
            result = ejudge.io.run(source, inputs, lang=lang.ref, raises=True)
            result.pprint()

            if expanded is None:
                expanded = result
                expanded_lang = lang
                self.source = expanded.source()
                self.needs_expansion = False
                self.validated_languages.add(lang)
            else:
                feedback = ejudge.io.grade(source, expanded, lang=lang.ref)
                if feedback.grade == 1:
                    self.validated_languages.add(lang)
                else:
                    self.invalid_languages.add(lang)
        self.save()

    def update_new_languages(self):
        """Like update_languages(), but only updates languages that were not
        validated before."""

        self.update_languages(self.get_new_languages())

    def __str__(self):
        return '%s (%s)' % (self.question.title, self.hash)


class CodeIoAnswerKey(models.Model):
    """Represents an answer to some question given in some specific computer
    language plus the placeholder text that should be displayed"""

    class Meta:
        verbose_name = _('answer key')
        verbose_name_plural = _('answer keys')
        unique_together = [('question', 'language')]

    question = models.ForeignKey(CodeIoQuestion, related_name='answer_keys')
    language = models.ForeignKey(ProgrammingLanguage)
    source = models.TextField(
            _('Answer source code'),
            blank=True,
            help_text=_('Source code for the correct answer in the given '
                        'programming language'),
    )
    placeholder = models.TextField(
            _('Placeholder source code'),
            blank=True,
            help_text=_('This optional field controls which code should be '
                        'placed in the source code editor when a question is '
                        'opened. This is useful to put boilerplate or even a '
                        'full program that the student should modify. It is '
                        'possible to configure a global per-language '
                        'boilerplate and leave this field blank.'),
    )

    def __str__(self):
        return str(self.language)

    @property
    def ref(self):
        return self.language.ref

    def grade(self, response):
        """Grade the given response object and return the corresponding
        CodeIoFeedback."""

        lang = self.language
        tree = self.question.expanded_tree
        source = response.text
        feedback = ejudge.io.grade(source, tree, lang=lang.ref)
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