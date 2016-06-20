import os
from django.utils.translation import ugettext_lazy as _
from codeschool import models
from codeschool.utils import lazy
from cs_activities.models import Activity, Response


# File-based activities
class FileItem(models.ListItemModel):
    """A file item for the FileDownloadActivity."""

    class Meta:
        root_field = 'activity'

    activity = models.ForeignKey('FileDownloadActivity')
    file = models.FileField(upload_to='file-activities/')
    name = models.TextField(blank=True)
    description = models.TextField(blank=True)

    # Derived properties
    size = property(lambda x: x.file.size)
    url = property(lambda x: x.file.url)
    open = property(lambda x: x.file.open)
    close = property(lambda x: x.file.close)
    save_file = property(lambda x: x.file.save)
    delete_file = property(lambda x: x.file.delete)

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = os.path.basename(self.file.name)
        super().save(*args, **kwargs)


class FileDownloadActivity(Activity):
    """
    Students complete this activity by downloading all provided files from the
    server.

    This activity allows teachers to share files with the students.
    """

    class Meta:
        verbose_name = _('file download list')
        verbose_name_plural = _('file download activities')

    provide_compressed = models.BooleanField(default=True)
    zip_file = models.FileField(blank=True, null=True)
    targz_file = models.FileField(blank=True, null=True)
    items = models.ListItemSequence.as_items(FileItem)
    files = lazy(lambda x: [item.file for item in x.items])


class UrlItem(models.ListItemModel):
    """
    An URL item for the UrlActivity.
    """
    class Meta:
        root_field = 'activity'

    activity = models.ForeignKey('UrlActivity')
    url = models.URLField()
    name = models.CharField(max_length=50, blank=True)
    alt = models.CharField(max_length=50, blank=True)


class UrlActivity(Activity):
    """
    Students complete this activity by opening the contents of all URLs in a
    page.

    This activity allows teachers to share a list of links with the students.
    """

    class Meta:
        verbose_name = _('URL list')
        verbose_name_plural = _('url list activities')

    items = models.ListItemSequence.as_items(UrlItem)
    urls = lazy(lambda x: [item.url for item in x.items])


# Text-based activities
class PageActivity(Activity):
    """
    Students complete this activity by seeing the content of a webpage defined
    in markdown.

    This activity allows teachers to share arbitrary content with the students.
    """

    body = models.TextField()


class SourceItem(models.ListItemModel):
    """A file item for the FileDownloadActivity."""

    class Meta:
        root_field = 'activity'

    activity = models.ForeignKey('SourceCodeActivity')
    format = models.ForeignKey(
        'cs_core.models.fileformat.FileFormat',
        verbose_name=_('format'),
        default='txt',
        help_text=_('The file format for the source code.'),
    )
    name = models.CharField(
        _('name'),
        max_length=140,
        help_text='A short description of the given source code fragment'
    )
    description = models.TextField(
        _('description'),
        blank=True,
        help_text=_(
            'A detailed description of the source code fragment. This field '
            'accepts Markdown.'
        )
    )
    source = models.TextField(
        _('source'),
        help_text=_('The source code fragment.')
    )
    visible = models.BooleanField(
        _('is visible'),
        default=True,
        help_text=_(
            'Non-visible source items are available for download, but are not '
            'included in the main page'),
    )

    def __str__(self):
        return self.name


class SourceCodeActivity(Activity):
    """
    Make a list of source code fragments available to students.

    This activity allows teachers to share text-based data and code with the
    students.
    """

    class Meta:
        verbose_name = _('source code fragment list')
        verbose_name_plural = _('source code fragment lists')

    items = models.ListItemSequence.as_items(SourceItem)


class SyncCodeEditItem(models.Model):
    """
    A simple state of the code in a SyncCodeActivity.
    """

    activity = models.ForeignKey('SyncCodeActivity', related_name='data')
    text = models.TextField()
    next = models.OneToOneField('self', blank=True, null=True,
                                related_name='previous')
    timestamp = models.DateTimeField(auto_now=True)

    @property
    def prev(self):
        try:
            return self.previous
        except ObjectDoesNotExist:
            return None


class SyncCodeActivity(Activity):
    """
    In this activity, the students follow a piece of code that someone
    edit and is automatically updated in all of student machines. It keeps
    track of all modifications that were saved by the teacher.
    """

    default_material_icon = 'code'
    language = models.ForeignKey('cs_core.ProgrammingLanguage')

    @property
    def last(self):
        try:
            return self.data.order_by('timestamp').last()
        except SyncCodeEditItem.DoesNotExist:
            return None

    @property
    def first(self):
        try:
            return self.data.order_by('timestamp').first()
        except SyncCodeEditItem.DoesNotExist:
            return None
