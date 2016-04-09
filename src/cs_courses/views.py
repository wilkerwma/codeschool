from collections import namedtuple
from django import http
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from srvice import srvice, Client
from codeschool.decorators import login_required, teacher_login_required
from codeschool.shortcuts import render_context, redirect, get_object_or_404
from cs_courses import models
from cs_activities.models import Activity


@login_required
def course_index(request):
    courses = request.user.enrolled_courses.all()
    return render_context(
        request, 'cs_courses/courses-index.jinja2',
        courses=courses
    )


@login_required
def course_detail(request, pk):
    course = get_object_or_404(models.Course, pk=pk)

    return render_context(
        request, 'cs_courses/course-detail.jinja2',
        course=course,
        user_activities=course.user_activities(request.user),

    )


@login_required
def course_add_activities(request, pk):
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


@srvice
def enable_activity(request, ref, when='now', selected=()):
    js = Client()

    if selected:
        js.refresh()

        course = get_object_or_404(models.Course, pk=ref)
        duration = course.activity_duration()

        for pk in selected:
            activity = Activity.objects.get_subclass(pk=pk)
            activity.reschedule_now(duration, update=True)
    return js


@csrf_protect
@teacher_login_required
def teacher_add_activities(request, pk):
    course = get_object_or_404(models.Course, pk=pk)

    if request.method != 'POST' or course.teacher != request.user:
        return http.HttpResponseForbidden()

    post = dict(request.POST)
    checked = [int(key[6:]) for key in post if key.startswith('check-')]
    activities = [get_object_or_404(Activity, pk=pk) for pk in checked]
    duration = course.activity_duration()
    start, end = course.next_time_slot()

    if 'add-now' in post:
        for activity in activities:
            activity.reschedule_now(duration)
            activity.save()
    elif 'add-next' in post:
        for activity in activities:
            activity.reschedule(start, end)
            activity.save()
    elif 'edit' in post:
        pass

    return redirect(course.get_absolute_url())


@login_required
def discipline_detail(request, id):
    raise NotImplementedError


@login_required
def activity_detail(request, pk):
    raise NotImplementedError


@login_required
def course_lessons(request, course_pk):
    """Shows a list of lessons for the given course"""

    course = get_object_or_404(models.Course, pk=course_pk)
    return render_context(
        request, 'cs_courses/lessons.jinja2',
        course=course,
        lessons=course.lessons,
        can_edit=request.user == course.teacher,
    )