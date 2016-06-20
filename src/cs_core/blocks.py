from django import forms
from wagtail.wagtailcore import blocks
from codeschool import blocks


@blocks.register_block
class SupportedLanguageChooserBlock(blocks.ChooserBlock):
    """
    Chooses a programming language in codeschool.
    """

    widget = forms.Select

    @property
    def target_model(self):
        from cs_core.models import ProgrammingLanguage

        SupportedLanguageChooserBlock.target_model = ProgrammingLanguage
        return ProgrammingLanguage

    def value_for_form(self, value):
        if isinstance(value, self.target_model):
            return value.pk
        else:
            return value
