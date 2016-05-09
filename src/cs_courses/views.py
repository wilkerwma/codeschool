from collections import namedtuple
from django import http
from srvice import srvice, Client
from codeschool.decorators import login_required
from codeschool.shortcuts import render_context, get_object_or_404, redirect
from cs_courses import models
from cs_activities.models import Activity


@login_required
def course_index(request):
    courses = (request.user.enrolled_courses.all() |
               request.user.owned_courses.all() |
               request.user.courses_as_staff.all()).distinct()

    open_courses = models.Course.objects\
        .filter(is_active=True)\
        .exclude(pk__in=courses)

    if request.method == 'POST':
        if request.POST['action'] == 'subscribe':
            course = models.Course.objects.get(pk=request.POST['course'])
            course.register_student(request.user)

    return render_context(
        request, 'cs_courses/course-index.jinja2',
        courses=courses,
        open_courses=open_courses,
    )


@login_required
def discipline_detail(request, id):
    raise NotImplementedError


@login_required
def course_detail(request, pk):
    course = get_object_or_404(models.Course, pk=pk)

    if request.method == 'POST':
        if request.POST['action'] == 'cancel-subscription':
            if request.user != course.teacher:
                course.students.remove(request.user)
                return redirect('../')
            else:
                raise RuntimeError('teachers cannot unsubscribe of their own '
                                   'courses')

    return render_context(
        request, 'cs_courses/course-detail.jinja2',
        course=course,
        role=course.role(request.user),
        user_activities=course.user_activities(request.user),

    )


@srvice
def enable_activity(request, ref, when='now', selected=()):
    js = Client()

    if selected:
        js.refresh()

        course = get_object_or_404(models.Course, pk=ref)
        duration = course.activity_duration()

        if course.teacher != request.user:
            raise PermissionError

        for pk in selected:
            activity = Activity.objects.get_subclass(pk=pk)
            activity.reschedule_now(duration, update=True)
    return js


@login_required
def add_activities(request, pk):
    course = get_object_or_404(models.Course, pk=pk)

    if request.user != course.teacher:
        return http.HttpResponseForbidden()

    T = namedtuple('ActivityType', ['name', 'url'])
    activity_types = \
        [T(tt._meta.verbose_name.title(), tt.__name__.lower())
         for tt in Activity.get_subclasses()]

    return render_context(
        request, 'cs_courses/add-activities.jinja2',
        course=course,
        past_activities = course.past_activities,
        pending_activities = course.pending_activities,
        activity_types=activity_types,
    )
