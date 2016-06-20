from django.utils.translation import ugettext_lazy as _
from wagtail.wagtailforms.models import AbstractEmailForm, AbstractFormField
from codeschool import panels
from codeschool import models


class FormField(AbstractFormField):
    page = models.ParentalKey('FormPage', related_name='form_fields')


class FormPage(AbstractEmailForm):
    intro = models.RichTextField(blank=True)
    thank_you_text = models.RichTextField(blank=True)

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