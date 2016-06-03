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
    file = models.FileField()


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


class SyncCodeEditItem(models.Model):
    """
    A simple state of the code in a SyncCodeActivity.
    """

    activity = models.ForeignKey(SyncCodeActivity, related_name='data')
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