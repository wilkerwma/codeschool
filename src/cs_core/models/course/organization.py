from django.utils.translation import ugettext_lazy as _
from django.apps import apps
from wagtail.wagtailcore.models import Orderable, Page
from codeschool import panels
from codeschool import models


class Faculty(models.DescribablePage):
    """
    Describes a faculty/department or any institution that is responsible for
    managing disciplines.
    """

    location_coords = models.CharField(
        _('coordinates'),
        max_length=255,
        blank=True,
        null=True,
        help_text=_(
            'Latitude and longitude coordinates for the faculty building. The '
            'coordinates are selected from a Google Maps widget.'
        ),
    )

    @property
    def courses(self):
        return apps.get_model('cs_core', 'Course').objects.filter(
            path__startswith=self.path
        )

    # Wagtail admin
    parent_page_types = ['wagtailcore.Page']
    subpage_types = None
    subpage_types = ['Discipline']
    content_panels = models.DescribablePage.content_panels + [
        panels.MultiFieldPanel([
            panels.FieldPanel('location_coords', classname="gmap"),
        ], heading=_('Location')),
    ]


class Discipline(models.DescribablePage):
    """
    A discipline represents one abstract academic discipline.

    Each discipline can be associated with many courses.
    """

    class Meta:
        parent_init_attribute = 'faculty'

    @property
    def faculty(self):
        return self.get_parent().faculty_instance

    @faculty.setter
    def faculty(self, value):
        self.set_parent(value)

    # Wagtail admin
    parent_page_types = ['Faculty']
    subpage_types = ['Course']


# We define these globals to avoid circular imports of the Course class
COURSE_CLS = None


def course_cls():
    global COURSE_CLS
    if COURSE_CLS is None:
        import cs_core.models.couCourse as COURSE_CLS
    return COURSE_CLS
