from django import forms
from django.utils.encoding import force_text
from wagtail.wagtailcore.blocks import FieldBlock


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
