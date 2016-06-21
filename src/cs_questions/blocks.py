from decimal import Decimal
from django.forms import widgets
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import force_text
from wagtail.wagtailcore import blocks
from codeschool import blocks
import cs_core.blocks


#
# Base blocks
#
class ResponseForm(forms.Form):
    """
    Base form class for fetching responses for AnswerBlocks.

    We must store the type and index for the block in a hidden input.
    """

    def to_json(self):
        """
        Convert validated form data to JSON.
        """
        if self.is_valid():
            return self.cleaned_data
        else:
            raise ValidationError(self.errors)


class AnswerBlock(blocks.StructBlock):
    """
    Base class for answer blocks.
    """

    response_form_class = ResponseForm

    name = blocks.CharBlock(
        verbose_name=_('name'),
        max_legth=200,
        required=True,
        help_text=_('A name used to display this field in forms.'),
    )
    description = blocks.CharBlock(
        verbose_name=_('description'),
        required=False,
        help_text=_(
            'The description text displayed bellow the form field.'
        )
    )
    value = blocks.DecimalBlock(
        verbose_name=_('value'),
        default=1.0,
        help_text=_(
            'Relative weight given to this answer in the question.'
        ),
    )
    ref = blocks.RandomIdBlock()

    def normalize_response(self, value, response):
        """
        Normalize the given response.

        `value` is the structure representing the AnswerBlock state saved by
        wagtail.
        """

        return response

    def autograde_response(self, value, response):
        """
        Grades a response. Return a value between 0-100.

        `value` is the structure representing the AnswerBlock state saved by
        wagtail.
        """

        raise NotImplemented

    def render(self, value):
        form = self.get_form(value)
        if form:
            return form.as_table()
        else:
            return super().render(value)

    def get_form(self, value):
        """
        Return an initialized response form for the object.
        """

        if self.response_form_class:
            form = self.response_form_class()
            response_field = form['response']
            response_field.name = '%s__%s' % (response_field.name, value['ref'])
            response_field.html_name = response_field.name
            response_field.label = value['name']
            return form
        return None


#
# Numeric responses
#
class NumericResponseForm(ResponseForm):
    response = forms.DecimalField()


class BooleanResponseForm(ResponseForm):
    response = forms.BooleanField()


@blocks.register_block
class NumericAnswerBlock(AnswerBlock):
    """
    Represents a numeric answer.
    """

    response_form_class = NumericResponseForm

    answer = blocks.DecimalBlock(
        required=True,
        help_text=_('The numerical value for the correct answer.'),
    )
    tolerance = blocks.DecimalBlock(
        default=0,
        help_text=_(
            'Tolerance around the correct answer in which responses are still '
            'considered to be correct.'
        ),
    )

    def normalize_response(self, value, response):
        return Decimal(response)

    def autograde_response(self, value, response):
        tolerance = Decimal(value['tolerance'])
        answer = Decimal(value['answer'])
        if abs(response - answer) <= tolerance:
            return Decimal(100)
        else:
            return Decimal(0)


@blocks.register_block
class BooleanAnswerBlock(AnswerBlock):
    """
    Represents a numeric answer.
    """

    response_form_class = BooleanResponseForm

    answer = blocks.BooleanBlock(
        required=True,
        help_text=_('Correct true/false answer.'),
    )


#
# Text-based responses
#
class TextResponseForm(ResponseForm):
    response = forms.CharField()


@blocks.register_block
class StringAnswerBlock(AnswerBlock):
    """
    Represents a numeric answer.
    """

    answer = blocks.TextBlock(
        required=True,
        help_text=_('String with the correct answer.'),
    )
    case_sensitive = blocks.BooleanBlock(
        default=False,
        help_text=_('If enabled, the response will be sensitive to the case.'),
    )
    use_regex = blocks.BooleanBlock(
        verbose_name=_('use regular expressions?'),
        default=False,
        help_text=_(
            'If enabled, the answer string is interpreted as a regular '
            'expression. A response is considered to be correct if it matches '
            'the regular expression. Remember to use both ^ and $ to match the'
            'begining and the end of the string, if that is desired.'
        )
    )
    multiple_lines = blocks.BooleanBlock(
        verbose_name=_('allow multiple lines?'),
        default=False,
        help_text=_(
            'If enabled, this will allow the user input multiple lines of '
            'text. It will also present <textarea> widget instead of a regular '
            '<input> text box.'
        )
    )


#
# Date/time responses
#
class DateResponseForm(ResponseForm):
    response = forms.DateField()


@blocks.register_block
class DateAnswerBlock(AnswerBlock):
    """
    Represents a numeric answer.
    """

    answer = blocks.DateBlock(
        required=True,
        help_text=_('Required date.'),
    )


#
# Utility functions
#
def get_response_form(block):
    """
    Return the response form associated with the given block.
    """