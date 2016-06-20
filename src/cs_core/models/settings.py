from django.utils.translation import ugettext_lazy as _
from wagtail.contrib.settings.models import BaseSetting, register_setting
from codeschool import models
from codeschool import panels as panels


@register_setting
class SocialPresenceSettings(BaseSetting):
    facebook = models.URLField(
        help_text='Your Facebook page URL'
    )
    instagram = models.CharField(
        max_length=255, help_text='Your Instagram username, without the @'
    )
    trip_advisor = models.URLField(
        help_text='Your Trip Advisor page URL'
    )
    youtube = models.URLField(
        help_text='Your YouTube channel or user account URL'
    )

    panels = [
        panels.FieldPanel('facebook'),
        panels.FieldPanel('instagram'),
        panels.FieldPanel('trip_advisor'),
    ]


@register_setting
class LoginSettings(BaseSetting):
    username_as_school_id = models.BooleanField(
        default=False,
        help_text=_(
            'If true, force the username be equal to the school id for all '
            'student accounts.'
        )
    )
    school_id_regex = models.TextField(
        default='',
        blank=True,
        help_text=_(
            'A regular expression for matching valid school ids. If blank, no'
            'check will be performed on the validity of the given school ids'
        ),
    )
    panels = [
        panels.MultiFieldPanel([
            panels.FieldPanel('username_as_school_id'),
            panels.FieldPanel('school_id_regex'),
        ], heading=_('School id configuration'))
    ]