"""
Core generic blocks.

I hope these will be merged in Wagtail in the future.
"""

import random
import string
from django import forms
from django.utils.html import escape
from django.utils.encoding import force_text
from wagtail.wagtailcore.blocks import FieldBlock, CharBlock

__all__ = ['IntegerBlock', 'FloatBlock', 'DecimalBlock', 'RandomIdBlock']


#
#
#
class NumericBlockBase(FieldBlock):
    """
    Base class for blocks of numeric types.
    """

    def get_searchable_content(self, value):
        return [force_text(value)]


class IntegerBlock(NumericBlockBase):
    def __init__(self, required=True, help_text=None, max_value=None, min_value=None, **kwargs):
        self.field = forms.IntegerField(
            required=required,
            help_text=help_text,
            max_value=max_value,
            min_value=min_value
        )
        super(IntegerBlock, self).__init__(**kwargs)


class FloatBlock(NumericBlockBase):
    def __init__(self, required=True, help_text=None, max_value=None, min_value=None, **kwargs):
        self.field = forms.FloatField(
            required=required,
            help_text=help_text,
            max_value=max_value,
            min_value=min_value
        )
        super(FloatBlock, self).__init__(**kwargs)


class DecimalBlock(NumericBlockBase):
    def __init__(self, required=True, help_text=None, max_value=None, min_value=None, decimal_places=None, **kwargs):
        self.field = forms.DecimalField(
            required=required,
            help_text=help_text,
            max_value=max_value,
            min_value=min_value,
            decimal_places=decimal_places
        )
        super(DecimalBlock, self).__init__(**kwargs)


#
# Random id strings
#
# We are using a very hackish solution. We implement an object that returns
# a random string each time a str(obj) is called. This happens to work with
# the wail wagtail produces the final HTML for the block.
ALPHABET = list(string.ascii_letters + string.digits + '_')


def random_hash():
    """
    A sufficiently long random string of text that makes it virtually
    impossible to obtain collisions.
    """

    # We have 10**18 possibilities!
    choice = '0'
    while choice[0].isdigit():
        choice = ''.join(random.choice(ALPHABET) for _ in range(10))
    return choice


class RandomHashString:
    def __str__(self):
        return random_hash()


#TODO: implement this correctly!
class RandomIdBlock(CharBlock):
    def __init__(self, *args, **kwargs):
        kwargs['default'] = RandomHashString()
        super().__init__(*args, **kwargs)
