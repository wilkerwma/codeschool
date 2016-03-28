from collections import namedtuple
from django.views.decorators.csrf import csrf_protect
from codeschool.decorators import login_required, teacher_login_required
from codeschool.shortcuts import render_context, redirect, get_object_or_404
from cs_courses import models
from cs_activities.models import Activity
from django import http


@csrf_protect
@teacher_login_required
def add_activities(request, pk):
    course = get_object_or_404(models.Course, pk=pk)

    if request.method != 'POST' or course.teacher != request.user:
        return http.HttpResponseForbidden()

    post = dict(request.POST)
    checked = [int(key[6:]) for key in post if key.startswith('check-')]
    activities = [get_object_or_404(Activity, pk=pk) for pk in checked]
    duration = course.default_duration()
    start, end = course.next_class()

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
def index(request):
    courses = request.user.enrolled_courses.all()
    return render_context(request, 'cs_courses/index.jinja2',
                          courses=courses)


@login_required
def discipline_detail(request, id):
    return render_context(request, 'base.jinja2')


@login_required
def course_detail(request, pk):
    course = get_object_or_404(models.Course, pk=pk)

    T = ActivityType
    activity_types = \
        [T(tt._meta.verbose_name, 'url') for tt in Activity.get_subclasses()]

    past_activities = pending_activities = []
    if course.teacher == request.user:
        past_activities = course.get_past_activities()
        pending_activities = course.get_pending_activities()

    return render_context(
        request, 'cs_courses/course.jinja2',
        course=course,
        activity_types=activity_types,
        past_activities=past_activities,
        pending_activities=pending_activities,
    )


@login_required
def activity_detail(request, pk):
    return render_context(request, 'cs_courses/activity.jinja2',
                          activity=get_object_or_404(models.Activity, pk=pk)
    )


ActivityType = namedtuple('ActivityType', ['name', 'url'])