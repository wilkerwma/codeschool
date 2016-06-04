from collections import namedtuple
from django import http
from django.utils.translation import ugettext_lazy as _
import srvice
from viewpack import CRUDViewPack, view
from codeschool.decorators import login_required
from codeschool.shortcuts import render_context, get_object_or_404, redirect
from cs_courses import models
from cs_activities.models import Activity


class CourseViewPack(CRUDViewPack):
    """
    Views for Course models, including a CRUD interface.
    """

    model = models.Course
    template_extension = '.jinja2'
    template_basename = 'cs_courses/'
    check_permissions = False
    raise_404_on_permission_error = True
    context_data = {
        'content_color': "#10A2A4",
        'object_name': _('poll'),
    }
    fields = ['discipline', 'start', 'end', 'students', 'staff', 'is_active']

    class DetailViewMixin:
        def get_context_data(self, **kwargs):
            user = self.request.user
            course = self.object
            return super().get_context_data(
                role=course.get_user_role(user),
                activities=course.get_user_activities(user),
                **kwargs
            )

    @view(pattern=r'^(?P<pk>\d+)/add-activity/$')
    def add_activity(self, request, pk):
        course = get_object_or_404(models.Course, pk=pk)

        if not course.can_edit(request.user):
            return http.HttpResponseForbidden()

        T = namedtuple('ActivityType', ['name', 'url'])
        activity_types = \
            [T(tt._meta.verbose_name.title(), tt.__name__.lower())
             for tt in Activity.get_subclasses()]

        return render_context(
            request, 'cs_courses/add-activity.jinja2',
            course=course,
            past_activities = course.past_activities.all(),
            pending_activities = course.pending_activities.all(),
            activity_types=activity_types,
        )
