from collections import namedtuple
from django import http
from django.utils.translation import ugettext_lazy as _
from django.template.loader import render_to_string
import srvice
from viewpack import CRUDViewPack, view, api, program
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

    @program(pattern=r'^(?P<pk>\d+)/add-activity/$')
    def add_activity(self, client, pk):
        course = get_object_or_404(models.Course, pk=pk)

        if not course.can_edit(client.user):
            raise PermissionError

        T = namedtuple('ActivityType', ['name', 'url'])
        activity_types = \
            [T(tt._meta.verbose_name.title(), tt.__name__.lower())
             for tt in Activity.get_subclasses()]

        client.dialog(
            html=render_to_string(
                'cs_courses/add-activity.jinja2',
                {
                    'course': course,
                    'past_activities': course.past_activities.all(),
                    'pending_activities': course.pending_activities.all(),
                    'activity_types': activity_types,
                },
                request=client.request,
            )
        )

    @api(pattern=r'^fib/$')
    def fib(*args):
        print('fib', args)
        self, request, N = args
        L = [1, 1]
        while len(L) < N:
            L.append(L[-1] + L[-2])
        return L[:N]


print(CourseViewPack.add_activity.pattern)
