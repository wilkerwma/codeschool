from codeschool import models
from codeschool import panels
from . import Activity


class SyncCodeEditItem(models.Orderable):
    """
    A simple state of the code in a SyncCodeActivity.
    """

    activity = models.ParentalKey(
        'SyncCodeActivity',
        related_name='items'
    )
    text = models.TextField()
    timestamp = models.DateTimeField(
        auto_now=True
    )

    # Wagtail admin
    panels = [
        panel.FieldPanel('text', widget=blocks.AceWidget()),
    ]


class SyncCodeActivity(Activity):
    """
    In this activity, the students follow a piece of code that someone
    edit and is automatically updated in all of student machines. It keeps
    track of all modifications that were saved by the teacher.
    """

    class Meta:
        verbose_name = _('synchronized code activity')
        verbose_name_plural = _('synchronized code activities')

    default_material_icon = 'code'
    language = models.ForeignKey(
        'ProgrammingLanguage',
        on_delete=models.PROTECT,
        related_name='sync_code_activities',
        help_text=_('Chooses the programming language for the activity'),
    )

    @property
    def last(self):
        try:
            return self.items.order_by('timestamp').last()
        except SyncCodeEditItem.DoesNotExist:
            return None

    @property
    def first(self):
        try:
            return self.items.order_by('timestamp').first()
        except SyncCodeEditItem.DoesNotExist:
            return None

    # Wagtail admin
    content_panels = models.CodeschoolPage.content_panels + [
        panel.MultiFieldPanel([
            panel.RichTextFieldPanel('short_description'),
            panel.FieldPanel('grading_method'),
            panel.FieldPanel('language'),
        ], heading=_('Options')),
        panel.InlinePanel('items', label='Items'),
    ]