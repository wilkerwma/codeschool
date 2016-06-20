from django.utils.translation import ugettext_lazy as _, ugettext as __
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from codeschool import models


@receiver(post_save, sender='cs_core.Course')
def save_gradebook(instance, created, **kwargs):
    if created:
         instance.add_child(instance=GradableList())


class GradableList(models.CodeschoolPage):
    """
    A page that displays the grades for all gradable activities that are
    computed into the final course grade.
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('title', __('Gradebook'))
        kwargs.setdefault('slug', 'gradebook')
        super().__init__(*args, **kwargs)


class GradableDefinition(models.Model):
    """
    Defines the how the grade for each specific activity will be computed.
    """
    course = models.ParentalKey(GradableList)

    @property
    def grades_page(self):
        return self.course.grades_page
