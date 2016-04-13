from collections import namedtuple
from django import http
from srvice import srvice, Client
from codeschool.decorators import login_required
from codeschool.models import User
from codeschool.shortcuts import render_context, render, get_object_or_404
from cs_courses import models
from cs_activities.models import Activity


@login_required
def course_index(request):
    courses = request.user.enrolled_courses.all()
    return render_context(
        request, 'cs_courses/course-index.jinja2',
        courses=courses
    )


@login_required
def discipline_detail(request, id):
    raise NotImplementedError


@login_required
def course_detail(request, pk):
    course = get_object_or_404(models.Course, pk=pk)

    return render_context(
        request, 'cs_courses/course-detail.jinja2',
        course=course,
        user_activities=course.user_activities(request.user),

    )


@login_required
def course_subscribe(request):
    context = dict(
        user=request.user,
        courses=models.Course.objects
            .filter(is_active=True)
            .exclude(pk__in=request.user.enrolled_courses.all())
    )
    return render(request, 'cs_courses/course-subscribe.jinja2', context)


@srvice
def do_subscribe(request, ref, selected=()):
    js = Client()

    if selected:
        if request.user.username != ref:
            raise PermissionError
        course = get_object_or_404(models.Course, pk=selected[0])
        course.students.add(request.user)
        js.refresh()
    else:
        js.dialog('close')
    return js


@srvice
def leave_course(request, user, course):
    js = Client()
    if request.user.username != user:
        raise PermissionError
    course = models.Course.objects.get(pk=course)
    course.students.remove(request.user)
    js.redirect('/courses/')
    return js


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
def activity_detail(request, pk):
    raise NotImplementedError


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
