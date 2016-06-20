from django.utils.translation import ugettext_lazy as _, ugettext as __
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.utils.text import slugify
from wagtail.wagtailcore import blocks
from codeschool import models
from codeschool import panels
from codeschool.utils import delegate_to


@receiver(post_save, sender='cs_core.LessonPage')
def save_lesson_page(instance, created, **kwargs):
    lesson_page = instance
    if created and not getattr(lesson_page, '_created_for_lesson', False):
        calendar = CalendarPage.objects.get(pk=lesson_page.get_parent().id)
        ordering = calendar.lessons.values_list('sort_order', flat=True)
        calendar.lessons.add(Lesson(
            title=lesson_page.title,
            page=lesson_page,
            sort_order=max(ordering) + 1,
        ))
        calendar.save()


@receiver(pre_save, sender='cs_core.Lesson')
def save_lesson(instance, **kwargs):
    lesson = instance
    if lesson.pk is None and lesson.page is None:
        lesson.page = lesson_page = LessonPage(
            title=lesson.title,
            slug=slugify(lesson.title),
            parent_page=lesson.calendar,
        )
        lesson_page._created_for_lesson = True
        lesson_page.save()


@receiver(post_save, sender='cs_core.Course')
def save_calendar(instance, created, **kwargs):
    if created:
        instance.add_child(instance=CalendarPage())


class CalendarPage(models.CodeschoolPage):
    """
    A page that gathers a list of lessons in the course.
    """

    @property
    def course(self):
        return self.get_parent()

    weekly_lessons = delegate_to('course')

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('title', __('Calendar'))
        kwargs.setdefault('slug', 'calendar')
        super().__init__(*args, **kwargs)

    def add_lesson(self, lesson, copy=True):
        """
        Register a new lesson in the course.

        If `copy=True` (default), register a copy.
        """

        if copy:
            lesson = lesson.copy()
        lesson.move(self)
        lesson.save()

    def new_lesson(self, *args, **kwargs):
        """
        Create a new lesson instance by calling the Lesson constructor with the
        given arguments and add it to the course.
        """

        kwargs['parent_node'] = self
        return Lesson.objects.create(*args, **kwargs)

    # Wagtail admin
    parent_page_types = ['cs_core.Course']
    subpage_types = ['cs_core.LessonPage']
    content_panels = models.CodeschoolPage.content_panels + [
        panels.InlinePanel(
            'lessons',
            label=_('Lessons'),
            help_text=_('List of lessons for this course.'),
        ),
    ]


class Lesson(models.Orderable):
    """
    Intermediate model between a LessonPage and a Calendar.
    """

    calendar = models.ParentalKey(
        'CalendarPage',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='lessons',
    )
    page = models.OneToOneField(
        'LessonPage',
        null=True,
        blank=True,
        related_name='lesson'
    )
    title = models.TextField(
        _('title'),
        help_text=_('A brief description for the lesson.'),
    )
    date = models.DateField(
        _('date'),
        null=True,
        blank=True,
        help_text=_('Date scheduled for this lesson.'),
    )

    panels = [
        panels.FieldPanel('title'),
        panels.FieldPanel('date'),
    ]


class LessonPage(models.CodeschoolPage):
    """
    A single lesson in an ordered list.
    """

    class Meta:
        verbose_name = _('Lesson')
        verbose_name_plural = _('Lessons')

    body = models.StreamField([
            ('paragraph', blocks.RichTextBlock()),
        ],
        blank=True,
        null=True
    )

    description = delegate_to('lesson')
    date = delegate_to('lesson')
    calendar = property(lambda x: x.get_parent())

    # Wagtail admin
    parent_page_types = ['cs_core.CalendarPage']
    subpage_types = []
    content_panels = models.CodeschoolPage.content_panels + [
        panels.StreamFieldPanel('body'),
    ]


class LessonPageProxy(LessonPage):
    class Meta:
        proxy = True

