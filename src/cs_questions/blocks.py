from decimal import Decimal
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import force_text
from wagtail.wagtailcore import blocks
from codeschool import blocks
import cs_core.blocks


#
# Simple answer blocks
#
class AnswerBlock(blocks.StructBlock):
    """
    Base class for answer blocks.
    """

    name = blocks.CharBlock(
        max_legth=200,
        required=True,
        help_text=_('A name used to display this field in forms.'),
    )
    value = blocks.FloatBlock(
        default=1.0,
        help_text=_(
            'Relative weight given to this answer in the question.'
        ),
    )


@blocks.register_block
class NumericAnswerBlock(AnswerBlock):
    """
    Represents a numeric answer.
    """

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


@blocks.register_block
class BooleanAnswerBlock(AnswerBlock):
    """
    Represents a numeric answer.
    """

    answer = blocks.BooleanBlock(
        required=True,
        help_text=_('Correct true/false answer.'),
    )


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
        help_text=_('If true, the response will be sensitive to the case.'),
    )
    use_regex = blocks.BooleanBlock(
        default=False,
        help_text=_(
            'If true, the answer string is interpreted as a regular '
            'expression. A response is considered to be correct if it matches '
            'the regular expression. Remember to use both ^ and $ to match the'
            'begining and the end of the string, if that is desired.'
        )
    )


@blocks.register_block
class DateAnswerBlock(AnswerBlock):
    """
    Represents a numeric answer.
    """

    answer = blocks.DateBlock(
        required=True,
        help_text=_('Required date.'),
    )