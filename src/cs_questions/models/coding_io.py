from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.html import mark_safe, escape
from django.utils.translation import ugettext_lazy as _

import ejudge
import iospec.feedback
import srvice
from codeschool import models
from codeschool import panels
from codeschool.forms import register_parent_prefetch
from codeschool.shortcuts import lazy
from codeschool.utils import md5hash
from cs_core.models import ProgrammingLanguage, programming_language, \
    bound_property
from cs_questions.models import Question, QuestionResponseItem, \
    register_response_item
from cs_questions.renderers import render_html
from iospec import parse_string as parse_iospec


# noinspection PyPropertyAccess
@register_parent_prefetch
class CodingIoQuestion(Question):
    """
    CodeIo questions evaluate source code and judge them by checking if the
    inputs and corresponding outputs match an expected pattern.
    """

    class Meta:
        verbose_name = _('input/output question')
        verbose_name_plural = _('input/output questions')

    iospec_size = models.PositiveIntegerField(
        _('number of iospec template expansions'),
        default=10,
        help_text=_(
            'The desired number of test cases that will be computed after '
            'comparing the iospec template with the answer key. This is only a '
            'suggested value and will only be applied if the response template '
            'uses input commands to generate random input.'),
    )
    iospec_source = models.TextField(
        _('response template'),
        help_text=_(
            'Template used to grade I/O responses. See '
            'http://pythonhosted.org/iospec for a complete reference on the '
            'template format.'),
    )
    iospec_hash = models.CharField(
        max_length=32,
        blank=True,
        help_text=_('A hash to keep track of iospec updates.'),
    )
    timeout = models.FloatField(
        _('timeout in seconds'),
        blank=True,
        default=1.0,
        help_text=_(
            'Defines the maximum runtime the grader will spend evaluating '
            'each test case.'
        ),
    )
    is_usable = models.BooleanField(
        _('is usable'),
        help_text=_(
            'Tells if the question has at least one usable iospec entry. A '
            'complete iospec may be given from a single iospec source or by a '
            'combination of a valid source and a reference computer program.'
        )
    )
    is_consistent = models.BooleanField(
        _('is consistent'),
        help_text=_(
            'Checks if all given answer keys are consistent with each other. '
            'The question might become inconsistent by the addition of an '
            'reference program that yields different results from the '
            'equivalent program in a different language.'
        )
    )

    @lazy
    def iospec(self):
        """
        The IoSpec structure corresponding to the iospec_source.
        """

        return parse_iospec(self.iospec_source)

    @property
    def is_answer_key_complete(self):
        """
        Return True if an answer key item exists for all programming languages.
        """

        refs = self.is_answer_keys.values('language__ref', flatten=True)
        all_refs = ProgrammingLanguage.objects.values('ref', flatten=True)
        return set(all_refs) == set(refs)

    @bound_property
    def language(self):
        """
        Instances can be bound to a programming language.
        """

        return getattr(self, '_language_bind', None)

    @language.setter
    def language(self, value):
        self._language_bind = programming_language(value, raises=False)

    @property
    def is_language_bound(self):
        return self.language is not None

    @property
    def default_language(self):
        """
        The main language associated with this question if a single answer key
        is defined.
        """

        return self.answer_key_items.get().language

    def _language(self, language=None, raises=True):
        # Shortcut used internally to normalize the given language
        if language is None:
            return self.language or self.default_language
        return programming_language(language, raises)

    def __init__(self, *args, **kwargs):
        # Supports automatic conversion between iospec data and iospec_source
        iospec = kwargs.pop('iospec', None)
        if iospec:
            kwargs['iospec_source'] = iospec.source()
            self.iospec = iospec
        super().__init__(*args, **kwargs)

    def clean(self):
        """
        Validate the iospec_source field.
        """

        super().clean()

        # We first should check if the iospec_source has been changed and thus
        # requires a possibly expensive validation.
        source = self.iospec_source
        iospec_hash = md5hash(source)
        if self.iospec_hash != iospec_hash:
            try:
                self.iospec = iospec.parse_string(self.iospec_source)
            except Exception:
                raise ValidationError(
                    {'iospec_source': _('invalid iospec syntax')}
                )
            else:
                self.iospec_hash = iospec_hash
                if self.pk is None:
                    self.is_usable = self.iospec.is_simple
                    self.is_consistent = True
                else:
                    self.is_usable = self._is_usable(self.iospec)
                    self.is_consistent = self._is_consistent(self.iospec)

    def _is_usable(self, iospec):
        """
        This function is triggered during the clean() validation when a new
        iospec data is inserted into the database.
        """

        # Simple iospecs are always valid since they can be compared with
        # arbitrary programs.
        if iospec.is_simple_io:
            return True

        # For now we reject all complex iospec structures
        return False

    def _is_consistent(self, iospec):
        """
        This function is triggered during the clean() validation when a new
        iospec data is inserted into the database.
        """

        # Simple iospecs always produce consistent answer keys since we prevent
        # invalid reference programs of being inserted into the database
        # during AnswerKeyItem validation.
        if iospec.is_simple_io:
            return True

        # For now we reject all complex iospec structures
        return False

    # Serialization methods: support markio and sets it as the default
    # serialization method for CodingIoQuestion's
    @classmethod
    def load_markio(cls, source):
        """
        Creates a CodingIoQuestion object from a Markio object or source
        string and saves the resulting question in the database.

        This function can run without touching the database if the markio file
        does not define any information that should be saved in an answer key.

        Args:
            source:
                A string with the Markio source code.

        Returns:
            question:
                A question object.
        """

        import markio

        if isinstance(source, markio.Markio):
            data = source
        else:
            data = markio.parse_string(source)

        # Create question object from parsed markio data
        question = CodingIoQuestion.objects.create(
            title=data.title,
            author_name=data.author,
            timeout=data.timeout,
            short_description=data.short_description,
            long_description=data.description,
            iospec_source=data.tests,
        )

        # Add answer keys
        answer_keys = {}
        for (lang, answer_key) in data.answer_key.items():
            language = programming_language(lang)
            key = question.answer_keys.create(language=language,
                                              source=answer_key)
            answer_keys[lang] = key
        for (lang, placeholder) in data.placeholder.items():
            if placeholder is None:
                continue
            try:
                answer_keys[lang].placeholder = placeholder
                answer_keys[lang].save(update_fields=['placeholder'])
            except KeyError:
                language = ProgrammingLanguage.objects.get(lang)
                question.answer_keys.create(
                    language=language,
                    placeholder=placeholder
                )
        return question

    @classmethod
    def load(cls, format='markio', **kwargs):
        return super().load(format=format, **kwargs)

    def dump_markio(self):
        """
        Serializes question into a string of Markio source.
        """

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

    def answer_key_item(self, language=None):
        """
        Return the AnswerKeyItem instance for the requested language or None if
        no object is found.
        """

        language = self._language(language)
        try:
            return self.answer_key_items.get(language=language)
        except AnswerKeyItem.DoesNotExist:
            return None

    def answer_key(self, language=None):
        """
        Return the answer key IoSpec object associated with the given language.
        """

        key = self.answer_key_item(language)
        if key is None or key.iospec_source is None:
            new_key = self.answer_key_item()
            if key == new_key:
                if self.iospec.is_simple:
                    raise ValueError('no valid iospec is defined for the '
                                     'question')
                return iospec.expand_inputs(self.iospec_size)
            key = new_key

        # We check if the answer key item is synchronized with the parent hash
        if key.iospec_hash != key.parent_hash():
            try:
                key.update(self.iospec)
            except ValidationError:
                return self.iospec
        return key.iospec

    def placeholder(self, language=None):
        """
        Return the placeholder text for the given language.
        """

        if key is None:
            return ''
        return key.placeholder

    def reference_source(self, language=None):
        """
        Return the reference source code for the given language or None, if no
        reference is found.
        """

        key = self.answer_key_item(language)
        if key is None:
            return ''
        return key.source

    def run_code(self, source=None, iospec=None, language=None):
        """
        Run the given source code string for the programming language using the
        default IoSpec.

        If no code string is given, runs the reference source code, it it
        exists.
        """

        if language is None:
            language = self.answer_key_items.get().language
        key = self.answer_key_item(language)
        return key.run(source, iospec)

    def update_iospec_source(self):
        """
        Updates the iospec_source attribute with the current iospec object.

        Any modifications made to `self.iospec` must be saved explicitly to
        persist on the database.
        """

        if 'iospec' in self.__dict__:
            self.iospec_source = self.iospec.source()

    def register_response_item(self, source, language=None, **kwargs):
        response_data = {
            'language': self._language(language).ref,
            'source': source,
        }
        kwargs.update(response_data=response_data)
        return super().register_response_item(**kwargs)

    # Serving pages and routing
    @srvice.route(r'^submit-response/$')
    def respond_route(self, client, source=None, language=None, **kwargs):
        """
        Handles student responses via AJAX and a srvice program.
        """

        if not language:
            client.dialog('<p>Please select the correct language</p>')
            return

        # Bug with <ace-editor>?
        if not source or source == '\x01\x01':
            client.dialog('<p>Internal error: please send it again!</p>')
            return

        language = programming_language(language)
        self.bind(client.request, language=language, **kwargs)
        response = self.register_response_item(source, autograde=True)
        html = render_html(response.feedback)
        client.dialog(html)

    @srvice.route(r'^placeholder/$')
    def get_placeholder_route(self, request, language):
        """
        Return the placeholder code for some language.
        """

        return self.get_placehoder(language)

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context['form'] = ResponseForm(request.POST)
        return context

    # Wagtail admin
    content_panels = Question.content_panels[:]
    content_panels.insert(-1, panels.MultiFieldPanel([
        panels.FieldPanel('iospec_size'),
        panels.FieldPanel('iospec_source'),
    ], heading=_('IoSpec definitions')))
    content_panels.insert(
        -1, panels.InlinePanel('answer_key_items',
                               label=_('Answer keys'))
    )


class AnswerKeyItem(models.Model):
    """
    Represents an answer to some question given in some specific computer
    language plus the placeholder text that should be displayed.
    """

    class ValidationError(Exception):
        pass

    class Meta:
        verbose_name = _('answer key')
        verbose_name_plural = _('answer keys')
        unique_together = [('question', 'language')]

    question = models.ParentalKey(
        CodingIoQuestion,
        related_name='answer_key_items'
    )
    language = models.ForeignKey(
        ProgrammingLanguage,
        related_name='answer_keys',
    )
    source = models.TextField(
        _('answer source code'),
        blank=True,
        help_text=_(
            'Source code for the correct answer in the given programming '
            'language.'
        ),
    )
    placeholder = models.TextField(
        _('placeholder source code'),
        blank=True,
        help_text=_(
            'This optional field controls which code should be placed in '
            'the source code editor when a question is opened. This is '
            'useful to put boilerplate or even a full program that the '
            'student should modify. It is possible to configure a global '
            'per-language boilerplate and leave this field blank.'
        ),
    )
    source_hash = models.CharField(
        max_length=32,
        blank=True,
        help_text=_('Hash computed from the reference source'),
    )
    iospec_hash = models.CharField(
        max_length=32,
        blank=True,
        help_text=_('Hash computed from reference source and iospec_size.'),
    )
    iospec_source = models.TextField(
        _('expanded source'),
        blank=True,
        help_text=_(
            'Iospec source for the expanded testcase. This data is computed '
            'from the reference iospec source and the given reference program '
            'to expand the outputs from the given inputs.'
        )
    )

    @lazy
    def iospec(self):
        return parse_iospec(self.iospec_source)

    iospec_size = property(lambda x: x.question.iospec_size)

    def clean(self):
        super().clean()

        if self.question is None:
            return

        # We only have to update if the parent's hash is incompatible with the
        # current hash and the source field is defined. We make this test to
        # perform the expensive code re-evaluation only when strictly necessary
        parent_hash = self.parent_hash()
        source_hash = md5hash(self.source)

        if parent_hash != self.iospec_hash or source_hash != self.source_hash:
            iospec = self.question.iospec
            result = self._update_state(iospec, self.source, self.language)
            self.iospec_source = result.source()
            self.source_hash = source_hash
            self.iospec_hash = parent_hash

    def update(self, commit=True):
        """
        Update the internal iospec source and hash keys to match the given
        parent iospec value.

        It raises a ValidationError if the source code is invalid.
        """

        iospec = self.question.iospec
        result = self._update_state(iospec, self.source, self.language)
        self.iospec_source = result.source()
        self.source_hash = md5hash(self.source)
        self.iospec_hash = self.parent_hash()
        if commit:
            self.save()

    def _update_state(self, iospec, source, language):
        """
        Worker function for the .update() and .clean() methods.

        Update the hashes and the expanded iospec_source for the answer key.
        """

        # We expand inputs and compute the result for the given source code
        # string
        language = language.ejudge_ref()
        if len(iospec) <= self.iospec_size:
            iospec.expand_inputs(self.iospec_size)
        result = run_code(source, iospec, language)

        # Check if the result has runtime or build errors
        if result.has_errors:
            error = {'error': result.get_error_message()}
            raise ValidationError({
                'source': mark_safe(_(
                    '"%(error)s" produced when running the source code.'
                ) % error)
            })

        # The source may run fine, but still give results that are inconsistent
        # with the given testcases. This will only be noticed if the user
        # provides at least one simple IO test case.
        for (expected, value) in zip(iospec, result):
            if expected.is_simple and expected != value:
                msg = _(
                    '<div class="error-message">'
                    'Your program produced invalid results in this tescase:\n'
                    '<br>\n'
                    '<pre>%(expected)s</pre>\n'
                    '<br>\n'
                    'got:\n'
                    '<pre>%(result)s<pre></div>'
                )
                error = {
                    'expected': escape(expected.source()),
                    'result': escape(value.source())
                }
                msg = mark_safe(msg % error)
                raise ValidationError({'source': msg})

        # Now we save the result because it has all the computed expansions
        return result

    def save(self, *args, **kwds):
        if 'iospec' in self.__dict__:
            self.iospec_source = self.iospec.source()
        super().save(*args, **kwds)

    def run(self, source=None, iospec=None):
        """
        Runs the given source against the given iospec.

        If no source is given, use the reference implementation.

        If no iospec is given, user the default. The user may also pass a list
        of input strings.
        """

        source = source or self.source
        iospec = iospec or self.iospec
        if not source:
            raise ValueError('a source code string must be provided.')

        return run_code(source, iospec, self.language.ejudge_ref())

    def parent_hash(self):
        """
        Return the iospec hash from the question current iospec/iospec_size.
        """

        parent = self.question
        return md5hash(parent.iospec_source + str(parent.iospec_size))

    def __repr__(self):
        return '<AnswerKey: %s, %s)' % (self.question, self.language)

    # Wagtail admin
    panels = [
        panels.FieldPanel('language'),
        panels.FieldPanel('source'),
        panels.FieldPanel('placeholder'),
    ]


@register_response_item(CodingIoQuestion)
class CodingIoResponseItem(QuestionResponseItem):
    """
    A response proxy class specialized in CodingIoQuestion responses.
    """
    class Meta:
        proxy = True

    @property
    def source(self):
        return self.response_data.get('source', '')

    @source.setter
    def source(self, value):
        self.response_data['source'] = value

    @property
    def language(self):
        try:
            lang_id = self.response_data['language']
            return ProgrammingLanguage.get_language(ref=lang_id)
        except (KeyError, ProgrammingLanguage.DoesNotExist):
            return None

    @language.setter
    def language(self, value):
        self.response_data['language'] = programming_language(value).ref

    # Feedback properties
    @lazy
    def feedback(self):
        if not self.feedback_data:
            return None

        data = dict(self.feedback_data)
        data['grade'] = self.final_grade / 100
        del data['source']
        del data['language']
        return iospec.feedback.Feedback.from_json(data)

    feedback_title = property(lambda x: x.feedback and x.feedback.title)
    feedback_testcase = property(lambda x: x.feedback and x.feedback.testcase)
    feedback_answer_key = property(lambda x: x.feedback and x.feedback.answer_key)
    feedback_hint = property(lambda x: x.feedback_data.get('hint'))
    feedback_message = property(lambda x: x.feedback_data.get('message'))
    feedback_status = property(lambda x: x.feedback_data.get('status'))

    @property
    def answer_key(self):
        return self.question.answer_key(self.language)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'feedback' in kwargs:
            self.update_feedback(feedback=kwargs['feedback'])

    def clean(self):
        super().clean()
        if self.feedback:
            data = self.feedback.to_json()
            del data['grade']
            self.feedback_data = data

    def autograde_compute(self):
        """
        Run code using the ejudge, saves the feedback and return the given
        grade.
        """

        # Compute feedback
        source = self.source
        language_ref = self.language.ejudge_ref()
        answer_key = self.answer_key
        feedback = grade_code(source, answer_key, lang=language_ref)

        # Save data and return grade
        self.update_feedback(feedback, update_grade=False)
        return self.feedback.grade * 100

    def update_feedback(self, feedback=None, update_grade=True):
        """
        Update feedback_data dictionary with info from feedback object
        """
        feedback = feedback or self.feedback

        self.feedback_data.update(
            answer_key=feedback.answer_key.to_json(),
            testcase=feedback.answer_key.to_json(),
            status=feedback.status,
        )
        if feedback.message:
            self.feedback_data['message'] = self.feedback.message
        if feedback.hint:
            self.feedback_data['hint'] = self.feedback.hint

        if update_grade:
            self.given_grade = feedback.grade * 100

        self.feedback = feedback


# We define a fake abstract model just to use the ModelForm class since it will
# be easier to re-use the automatic model than to create the ForeignKey form
# field by hand.
class ResponseModel(models.Model):
    class Meta:
        abstract = True

    language = models.ForeignKey(
        ProgrammingLanguage,
        verbose_name=_('Programming language'),
        help_text=_('The programming language for your code')
    )


class ResponseForm(forms.ModelForm):
    class Meta:
        model = ResponseModel
        fields = ['language']


#
# Utility functions
#
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


