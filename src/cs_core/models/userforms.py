from django.utils.translation import ugettext_lazy as _
from modelcluster.fields import ParentalKey
from wagtail.wagtailcore.fields import RichTextField
from wagtail.wagtailforms.models import AbstractEmailForm, AbstractFormField
from codeschool import panels


class FormField(AbstractFormField):
    page = ParentalKey('FormPage', related_name='form_fields')


class FormPage(AbstractEmailForm):
    intro = RichTextField(blank=True)
    thank_you_text = RichTextField(blank=True)

    content_panels = AbstractEmailForm.content_panels + [
        panels.FieldPanel('intro', classname="full"),
        panels.InlinePanel('form_fields', label="Form fields"),
        panels.FieldPanel('thank_you_text', classname="full"),
        panels.MultiFieldPanel([
            panels.FieldPanel('to_address', classname="full"),
            panels.FieldPanel('from_address', classname="full"),
            panels.FieldPanel('subject', classname="full"),
        ], heading=_("Email"))
    ]