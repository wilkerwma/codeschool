import hashlib
from iospec import parse_string as parse_iospec, SimpleTestCase
import iospec.feedback
import ejudge
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from model_utils import FieldTracker
from codeschool import models
from codeschool.db import saving
from codeschool.shortcuts import lazy, render_html
from cs_core.models import ProgrammingLanguage, programming_language, get_languages
from cs_questions.models.base import (Question, QuestionActivity,
                                      QuestionResponse)


class CodingIoQuestion(Question, models.StatusModel):
    """
    CodeIo questions evaluate source code and judge them by checking if the
    inputs and corresponding outputs match an expected pattern.
    """

    STATUS_INVALID = 'invalid'
    STATUS_UGLY = 'ugly'
    STATUS_DIRTY = 'dirty'
    STATUS_VALID = 'valid'
    STATUS_INCOMPLETE = 'incomplete'
    STATUS = models.Choices(
        (STATUS_INCOMPLETE, _('is not yet fully initialized')),
        (STATUS_INVALID, _('no valid answers')),
        (STATUS_UGLY, _('inconsistent answers')),
        (STATUS_DIRTY, _('some valid answers')),
        (STATUS_VALID, _('valid')),
    )
    iospec_size = models.PositiveIntegerField(
        _('number of iospec template expansions'),
        default=0,
        blank=True,
        help_text=_('The desired number of test cases that will be computed'
                    'after comparing the iospec template with the answer key.'
                    'This is only a suggested value and will only be applied if'
                    'the response template uses input commands to generate'
                    'random input.'),
    )
    iospec_source = models.TextField(
        _('response template'),
        blank=True,
        help_text=_('Template used to grade I/O responses. See '
                    'http://pythonhosted.org/iospec for a complete reference '
                    'on the template format.'),
    )
    timeout = models.FloatField(
            _('timeout in seconds'),
            blank=True,
            default=5.0,
            help_text=_('Defines the maximum runtime the grader will spend '
                        'evaluating each test case.'),
    )
    tracker = FieldTracker()

    @property
    def iospec(self):
        """The IoSpec structure corresponding to the iospec_source."""

        return parse_iospec(self.iospec_source)

    @property
    def hash(self):
        """The hash for the iospec_source string. This hash is compared to a
        hash registered to each answer key to check if it has the most current
        iospec data."""

        return md5hash(self.iospec_source + str(self.iospec_size))

    @property
    def is_answer_key_complete(self):
        """Return True if an answer key exists for all programming languages."""

        refs = self.is_answer_keys.values('language__ref', flatten=True)
        all_refs = ProgrammingLanguage.objects.values('ref', flatten=True)
        return set(all_refs) == set(refs)

    class Meta:
        app_label = 'cs_questions'
        verbose_name = _('input/output question')
        verbose_name_plural = _('input/output questions')

    # Importing and exporting
    @classmethod
    def from_markio(cls, source, commit=None, return_keys=False):
        """Creates a CodingIoQuestion object from a Markio object r source
        string and saves the resulting question in the database.

        This function can run without touching the database if the markio file
        does not define any information that should be saved in an answer key.

        Args:
            source:
                A string with the Markio source code.
            commit (bool):
                If True (default), saves resulting question in the database.
            return_keys (bool):
                If True, also return a dictionary mapping language references
                to answer keys.

        Returns:
            question:
                A question object.
            [answer_keys]:
                A map from language references to :class:`AnswerKeyItem`
                objects.
        """

        import markio

        if isinstance(source, markio.Markio):
            data = source
        else:
            data = markio.parse_string(source)

        # Create question object from parsed markio data
        question = CodingIoQuestion(
            title=data.title,
            author_name=data.author,
            timeout=data.timeout,
            short_description=data.short_description,
            long_description=data.description,
            iospec_source=data.tests,
        )
        saving(question, commit)

        # Add answer keys
        answer_keys = {}
        for (lang, answer_key) in data.answer_key.items():
            language = programming_language(lang)
            key = saving(CodingIoAnswerKey(question=question,
                                           language=language,
                                           source=answer_key), commit)
            answer_keys[lang] = key
        for (lang, placeholder) in data.placeholder.items():
            if placeholder is None:
                continue
            try:
                answer_keys[lang].placeholder = placeholder
                saving(answer_keys[lang], commit, update_fields=['placeholder'])
            except KeyError:
                language = ProgrammingLanguage.objects.get(lang)
                key = CodingIoAnswerKey(question=question,
                                        language=language,
                                        placeholder=placeholder)
                saving(key, commit)

        # Question is done!
        if return_keys:
            answer_keys = {key.language.ref: key
                           for key in answer_keys.values()}
            return question, answer_keys
        return question

    @classmethod
    def from_data(cls, source):
        """Return a new CodingIoQuestion instance from a string of Markio
        data. This API is used by the HasUploadMixin in the create view."""

        return cls.from_markio(source.decode('utf8'))

    def to_markio(self):
        """Serializes question into a string of Markio source."""

        import markio

        tree = markio.Markio(
            title=self.name,
            author=self.author_name,
            timeout=self.timeout,
            short_description=self.short_description,
            description=self.long_description,
            tests=self.iospec_source,
        )

        for key in self.answer_keys.all():
            tree.add_answer_key(key.source, key.language.ref)
            tree.add_placeholder(key.placeholder, key.language.ref)

        return tree.source()

    def to_data(self, type=None):
        """Render question as a Markio source. This API is used by the
        DetailView in the CRUD interface."""

        if type in (None, 'markio'):
            return self.to_markio()
        else:
            return NotImplemented

    # Validation
    def update(self, save=True, validate=True):
        """Update and validate all answer keys."""

        exception = None
        expanded_sources = {}
        invalid_languages = set()
        valid_languages = set()

        def validate_answer_keys():
            nonlocal exception

            for key in self.answer_keys.all():
                try:
                    if not key.is_update:
                        key.question = self
                        key.update(save, validate)
                    if not key.is_valid:
                        invalid_languages.add(key.language.ref)
                    elif key.source:
                        valid_languages.add(key.language.ref)
                except key.ValidationError as ex:
                    exception = ex
                    exception.__traceback__ = exception.__traceback__
                if key.iospec_source:
                    expanded_sources[key.language.ref] = key.iospec_source

            if len(expanded_sources) == 0:
                self.status = 'invalid'
            elif len(set(expanded_sources.values())) != 1:
                self.status = 'ugly'
            elif invalid_languages:
                if valid_languages:
                    self.status = 'dirty'
                else:
                    self.status = 'invalid'
            else:
                self.status = 'valid'

        # Save fields if rollback is necessary
        iospec_source = self.iospec_source
        iospec_size = self.iospec_size
        has_changed = (self.tracker.has_changed('iospec_source') or
                       self.tracker.has_changed('iospec_size'))

        # If fields had changed, update and restore original values
        if has_changed:
            self.save(update_fields=['iospec_source', 'iospec_size'])
            try:
                validate_answer_keys()
            finally:
                if not save:
                    self.iospec_size = iospec_size
                    self.iospec_source = iospec_source
                    self.save(update_fields=['iospec_source', 'iospec_size'])
        else:
            validate_answer_keys()

        # Force save if necessary
        if save:
            self.save()

    def update_keys(self):
        """Update all keys that were not updated."""

        for key in self.answer_keys.exclude(iospec_hash=self.hash):
            key.update(validate=False)

    def get_validation_errors(self, lang=None, test_iospec=True):
        """Raise ValueError if some answer key is invalid or produce
         invalid iospec expansions.

         Return a valid iospec tree expansion or None if no expansion was
         possible (e.g., by the lack of source code in the answer key)."""

        # It cannot be valid if the iospec source does not not parse
        if test_iospec:
            try:
                tree = parse_iospec(self.iospec)
            except SyntaxError as ex:
                raise ValueError('invalid iospec syntax: %s' % ex)

        # Expand to all langs if lang is not given
        if lang is None:
            keys = self.answer_keys.exclude(source='')
            langs = keys.values_list('language', flat=True)
            expansions = [self.is_valid(lang, test_iospec=False)
                          for lang in langs]
            if not expansions:
                return None
            if iospec.ioequal(expansions):
                return expansions[0]

        # Test an specific language
        if isinstance(lang, str):
            lang = ProgrammingLanguage.get(ref=lang)
        try:
            key = self.answer_keys.get(language=lang)
        except self.DoesNotExist:
            return None

        if key.source:
            result = run_code(key.source, key, lang=lang.ref)
            if result.has_errors():
                raise result.get_exception()
            return result
        else:
            return None

    # Other API
    def get_placeholder(self, lang):
        """Return the placeholder text for the given language."""

        if isinstance(lang, str):
            try:
                lang = ProgrammingLanguage.objects.get(ref=lang)
            except ProgrammingLanguage.DoesNotExist:
                return ''
        try:
            key = self.answer_keys.get(language=lang)
            return key.placeholder
        except CodingIoAnswerKey.DoesNotExist:
            return ''

    def grade(self, response, error=None):
        """Grade the given response object and return the corresponding
        feedback object."""

        try:
            key = self.answer_keys.get(language=response.language)
            key.assure_is_valid(error)
            iospec_data = key.iospec
        except CodingIoAnswerKey.DoesNotExist:
            self.update_keys()

            # Get all sources
            iospec_sources = self.answer_keys.filter(is_valid=True)\
                .values_list('iospec_source', flat=True)
            iospec_sources = set(iospec_sources)

            # Check if there is only a single distinct source
            if not iospec_sources:
                iospec_data = self.iospec.copy()
                iospec_data.expand_inputs()
                if not all(isinstance(x, SimpleTestCase) for x in iospec_data):
                    raise (
                        error or
                        CodingIoAnswerKey.ValidationError(iospec_data.pformat())
                    )
            elif len(iospec_sources) == 1:
                iospec_data = parse_iospec(next(iter(iospec_sources)))
            else:
                raise error or CodingIoAnswerKey.ValidationError(iospec_sources)

        # Construct ejudge feedback object
        lang = response.language.ref
        source = response.source
        return grade_code(source, iospec_data, lang=lang)


class CodingIoAnswerKey(models.Model):
    """Represents an answer to some question given in some specific computer
    language plus the placeholder text that should be displayed"""

    class ValidationError(Exception):
        pass

    class Meta:
        app_label = 'cs_questions'
        verbose_name = _('answer key')
        verbose_name_plural = _('answer keys')
        unique_together = [('question', 'language')]

    question = models.ForeignKey(CodingIoQuestion, related_name='answer_keys')
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
    is_valid = models.BooleanField(default=False)
    iospec_hash = models.CharField(max_length=32, blank=True)
    iospec_source = models.TextField(blank=True)

    def __str__(self):
        return 'AnswerKey(%s, %s)' % (self.question, self.language)

    def save(self, *args, **kwds):
        if 'iospec' in self.__dict__:
            self.iospec_source = self.iospec.source()
        super().save(*args, **kwds)

    @lazy
    def iospec(self):
        return parse_iospec(self.iospec_source)

    @property
    def is_update(self):
        return self.iospec_hash == self.compute_iospec_hash()

    @property
    def status(self):
        if not self.is_valid:
            return 'invalid'
        elif not self.is_update:
            return 'pending'
        else:
            return 'valid'

    def assure_is_valid(self, error=None):
        """Raises an error if key is invalid or cannot be updated."""

        if not self.is_update:
            self.update()
        if not self.is_valid:
            raise error or self.ValidationError

    def compute_iospec_hash(self):
        """
        Return the iospec hash from the question current iospec/iospec_size.
        """

        return self.question.hash

    def update(self, save=True, validate=True):
        """
        Force update of answer key by running the source code against the most
        recent iospec template in the parent question.

        This method saves the result in the database unless save=False.
        """

        self.iospec_hash = self.compute_iospec_hash()

        if self.source:
            iospec_data = self.question.iospec.copy()
            iospec_data.expand_inputs(self.question.iospec_size)
            source = self.source
            lang = self.language.ref
            self.iospec = run_code(source, iospec_data, lang=lang)
            self.is_valid = not self.iospec.has_errors()
        else:
            self.iospec_source = ''
            self.is_valid = True

        if save:
            self.save()

        if validate and self.is_valid is False:
            raise self.ValidationError('could not validate Answer key')


class CodingIoResponse(QuestionResponse):
    source = models.TextField(blank=True)
    language = models.ForeignKey(ProgrammingLanguage)

    # Feedback properties
    feedback = property(lambda x: x.feedback_data)
    feedback_title = property(lambda x: x.feedback_data.title)
    testcase = property(lambda x: x.feedback_data.testcase)
    answer_key = property(lambda x: x.feedback_data.answer_key)
    is_correct = property(lambda x: x.feedback_data.is_correct)

    def autograde_compute(self):
        self.feedback_data = self.question.grade(self)
        return self.feedback_data.grade * 100

    def html_feedback(self):
        if self.is_done:
            return render_html(
                self.feedback,
                template_name='cs_questions/render/feedback.jinja2')
        else:
            return super().html_feedback()

    @classmethod
    def _recompute_all_responses(cls):
        for r in cls.objects.all():
            r.grade = r.get_grade_from_feedback()
            r.save()


class CodingIoActivity(QuestionActivity):
    language = models.ForeignKey(ProgrammingLanguage)


# Utility functions
def md5hash(st):
    """Compute the hex-md5 hash of string.

    Returns a string of 32 ascii characters."""

    return hashlib.md5(st.encode('utf8')).hexdigest()


def run_code(source, inputs, lang=None):
    """Runs source code with given inputs and return the corresponding IoSpec
    tree."""

    return ejudge.io.run(source, inputs, lang,
                         raises=False,
                         sandbox=settings.CODESCHOOL_USE_SANDBOX)


def grade_code(source, answer_key, lang=None):
    """Compare results of running the given source code with the iospec answer
    key."""

    return ejudge.io.grade(source, answer_key, lang,
                           raises=False,
                           sandbox=settings.CODESCHOOL_USE_SANDBOX)

# Set the correct response class
CodingIoQuestion.response_cls = CodingIoResponse
