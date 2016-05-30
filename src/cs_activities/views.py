import srvice
from django import http
from django.utils.translation import ugettext_lazy as _
from cs_activities import models
from viewpack import InheritanceCRUDViewPack, CRUDViewPack


class ActivityCRUD(InheritanceCRUDViewPack):
    model = models.Activity
    template_extension = '.jinja2'
    template_basename = 'cs_activities/'
    check_permissions = True
    raise_404_on_permission_error = True
    context_data = {
        'content_color': "#589cbc",
        'set object_name': _('activity'),
    }
    exclude_fields = ['published_at', 'parent', 'icon_src']


@ActivityCRUD.register
class GenericActivityViews(CRUDViewPack):
    model = models.Activity


@ActivityCRUD.register
class SyncCodeActivityViews(CRUDViewPack):
    model = models.SyncCodeActivity
    template_basename = 'cs_activities/sync-code/'


@srvice.api
def code_sync_update(request, pk=None, data=None):
    # Check permissions
    activity = models.SyncCodeActivity.objects.get(pk=pk)
    if not activity.can_edit(request.user):
        return http.HttpResponseForbidden()

    # Add content only if it changes the last update
    last = activity.last
    if last is None or last.text != data:
        new = activity.data.create(text=data)
        if last is not None:
            last.next = new
            last.save(update_fields=['next'])


@srvice.api
def code_sync_remove(request, pk=None, item=None):
    # Check permissions
    activity = models.SyncCodeActivity.objects.get(pk=pk)
    if not activity.can_edit(request.user):
        return http.HttpResponseForbidden()

    item = activity.data.get(pk=item)
    result = None
    if item is None:
        return None

    if item.prev:
        item.prev.next = item.next
        item.prev.save(update_fields='next')
        result = item.pk
    elif item.next:
        result = item.next.pk

    if item:
        item.delete()


@srvice.api
def code_sync_get(request, pk=None, item=None, jump=None):
    # Check permissions
    activity = models.SyncCodeActivity.objects.get(pk=pk)
    if not activity.can_view(request.user):
        return http.HttpResponseForbidden()

    # Retrieve special jumps
    if jump == 'last':
        return [getattr(activity.last, 'pk', None),
                getattr(activity.last, 'text', '')]
    elif jump == 'first':
        return [getattr(activity.first, 'pk', None),
                getattr(activity.first, 'text', '')]

    # Retrieve content
    item = activity.data.get(pk=item)

    if jump == 'next' and item.next is not None:
        item = item.next
    elif jump == 'prev' and item.prev is not None:
        item = item.prev

    return [getattr(item, 'pk', None), getattr(item, 'text', '')]