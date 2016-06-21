from decimal import Decimal
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
import srvice
from codeschool import models
from codeschool import blocks
from codeschool import panels
from codeschool.shortcuts import lazy
from cs_questions.models import Question, QuestionResponseItem, \
    register_response_item
import cs_questions.blocks
NOT_PROVIDED = object()


class FormQuestion(Question):
    """
    FormQuestion's defines a question with multiple fields that can be
    naturally represented in a web form. A FormQuestion thus expect a response
    """
    body = models.StreamField([
            ('numeric', blocks.NumericAnswerBlock()),
            ('boolean', blocks.BooleanAnswerBlock()),
            ('string', blocks.StringAnswerBlock()),
            ('date', blocks.DateAnswerBlock()),
            ('content', blocks.StreamBlock([
                ('description', blocks.RichTextBlock()),
                ('code', blocks.CodeBlock()),
                ('markdown', blocks.MarkdownBlock()),
                ('image', blocks.ImageChooserBlock()),
                ('document', blocks.DocumentChooserBlock()),
                ('page', blocks.PageChooserBlock()),
            ])),
        ],
        verbose_name=_('Fields'),
        help_text=_(
            'You can insert different types of fields for the student answers. '
            'This works as a simple form that accepts any combination of the'
            'different types of answer fields.'
        )
    )

    def clean(self):
        super().clean()
        data = list(self.form_values())
        if not data:
            raise ValidationError({
                'body': _('At least one form entry is necessary.'),
            })

        # Test if ref keys are unique: when we implement this correctly, there
        # will have a 1 in 10**19 chance of collision. So we wouldn't expect
        # this to ever fail.
        ref_set = {value['ref'] for value in data}
        if len(ref_set) < len(data):
            raise ValidationError({
                'body': _('Answer block ref keys are not unique.'),
            })

    def register_response_item(self, raw_data=None, **kwargs):
        # Transform all values received as strings and normalize them to the
        # correct python objects.
        if raw_data is not None:
            response_data = {}
            children = self.stream_children_map()
            for key, value in raw_data.items():
                child = children[key]
                block = child.block
                blk_value = child.value
                response_data[key] = block.normalize_response(blk_value, value)
            kwargs['response_data'] = response_data
        return super().register_response_item(**kwargs)

    def stream_children(self):
        """
        Iterates over AnswerBlock based stream children.
        """

        return (blk for blk in self.body if blk.block_type != 'content')

    def stream_items(self):
        """
        Iterates over pairs of (key, stream_child) objects.
        """

        return ((blk.value['ref'], blk) for blk in self.stream_children())

    def form_values(self):
        """
        Iterate over all values associated with the question AnswerBlocks.
        """

        return (blk.value for blk in self.stream_children())

    def form_blocks(self):
        """
        Iterate over all AnswerBlock instances in the question.
        """

        return (blk.block for blk in self.stream_children())

    def stream_child(self, key, default=NOT_PROVIDED):
        """
        Return the StreamChild instance associated with the given key.

        If key is not found, return the default value, if given, or raises a
        KeyError.
        """

        for block in self.body:
            if block.block_type != 'content' and block.value['ref'] == key:
                return block

        if default is NOT_PROVIDED:
            raise KeyError(key)
        return default

    def form_block(self, key, default=NOT_PROVIDED):
        """
        Return the AnswerBlock instance for the given key.
        """

        try:
            return self.stream_child(key).block
        except KeyError:
            if default is NOT_PROVIDED:
                raise
            return default

    def form_value(self, ref, default=NOT_PROVIDED):
        """
        Return the form data for the given key.
        """

        try:
            return self.stream_child(key).value
        except KeyError:
            if default is NOT_PROVIDED:
                raise
            return default

    def stream_children_map(self):
        """
        Return a dictionary mapping keys to the corresponding stream values.
        """

        return {blk.value['ref']: blk for blk in self.body}

    # Serving pages and routing
    @srvice.route(r'^submit-response/$')
    def respond_route(self, client, **kwargs):
        """
        Handles student responses via AJAX and a srvice program.
        """

        data = {}
        for key, value in kwargs.items():
            if key.startswith('response__') and value:
                key = key[10:]  # strips the heading 'response__'
                data[key] = value

        response_item = self.register_response_item(
            raw_data=data,
            user=client.user,
            autograde=True
        )
        client.dialog(html=response_item.html_feedback())

    def get_response_form(self):
        block = self.body[0]
        return block.render()

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context['form'] = self.get_response_form()
        return context

    # Wagtail admin
    parent_page_types = ['cs_core.Faculty']
    content_panels = Question.content_panels[:]
    content_panels.insert(-1, panels.StreamFieldPanel('body'))


@register_response_item(FormQuestion)
class FormResponseItem(QuestionResponseItem):
    """
    A response to a FormQuestion.

    The response is stored internally in JSON as a list of block responses:

    """

    class Meta:
        proxy = True

    def __init__(self, *args, **kwargs):
        responses = kwargs.get('responses', None)
        if responses is not None:
            kwargs.setdefault('response_data', responses)
        super().__init__(*args, **kwargs)

    @property
    def responses(self):
        return self.response_data

    @responses.setter
    def responses(self, value):
        # Atomic operation
        old_data, self.response_data = self.response_data, {}
        try:
            for k, v in value.items():
                self.add_response(k, v)
        except:
            self.response_data = old_data
            raise

    def add_response(self, key, response):
        """
        Register a response to a given response block.
        """

        stream_child = self.question.stream_child(key)
        block = stream_child.block
        value = stream_child.value
        response = block.normalize_response(value, response)
        self.response_data[key] = response

    def autograde_compute(self):
        """
        The final grade is the weighted average over all responses normalized
        to 100.
        """

        total = Decimal(0)
        achieved = Decimal(0)
        response_data = self.response_data or {}
        for key, stream_child in self.question.stream_items():
            response = response_data.get(key, None)
            value = stream_child.value
            weight = Decimal(value.get('value', 1.0))
            total += weight
            if response is not None:
                block = stream_child.block
                response = block.normalize_response(value, response)
                achieved += weight * block.autograde_response(value, response)

        return achieved / total

