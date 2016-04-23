import srvice
from django import http
from cs_activities import models
from codeschool.urlsubclassmapper import MultiViews, MultiViewTypeDispatcher


class ActivityViews(MultiViewTypeDispatcher):
    model = models.Activity


@ActivityViews.register('generic')
class GenericActivityViews(MultiViews):
    model = models.Activity
    exclude = ['published_at']


@ActivityViews.register('sync-code')
class SyncCodeActivityViews(MultiViews):
   model = models.SyncCodeActivity
   exclude = ['published_at', 'parent']
   template_base = 'cs_activities/sync-code/'


@srvice.srvice
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


@srvice.srvice
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


@srvice.srvice
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

    return [getattr(item, 'pk', None),
            getattr(item, 'text', '')]