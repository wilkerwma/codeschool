from django.contrib.auth.models import User
from django import http
from codeschool.shortcuts import render_context
from codeschool.decorators import login_required
from cs_questions import models

users = User.objects
type_map = {}


def register_question_type(tt, name, cls=None, *, detail=None, new=None, **kwds):
    """
    Register question type.
    """

    def make_action(name):
        def action_func(request, obj, *args, **kwds):
            manager = cls()
            method = login_required(getattr(manager, name))
            return method(request, obj, *args, **kwds)
        return action_func

    if cls:
        for action in dir(cls):
            if action.startswith('_'):
                continue
            elif action == 'new' and not new:
                new = lambda r: login_required(cls().new)(r)
            elif action == 'detail' and not detail:
                detail = lambda r, o: login_required(cls().detail)(r, o)
            else:
                kwds[action.replace('_', '-')] = make_action(action)

    kwds.update(new=new, view=detail)
    kwds = {k: v for (k, v) in kwds.items() if v is not None}
    type_map[tt] = kwds
    type_map[name] = kwds


def index(request):
    return render_context(
        request,
        'cs_questions/index.jinja2',
        questions=models.Question.objects.all().order_by('pk')
    )


def question_detail(request, pk):
    try:
        obj = models.Question.objects.get_subclass(pk=pk)
    except models.Question.DoesNotExist:
        raise http.Http404
    return type_map[type(obj)]['view'](request, obj)


def question_action(request, pk, action):
    action, *args = action.split('/')
    try:
        obj = models.Question.objects.get_subclass(pk=pk)
    except models.Question.DoesNotExist:
        raise http.Http404('no question with pk=%s found.' % pk)
    return type_map[type(obj)][action](request, obj, *args)


def question_new(request, type_name):
    return type_map[type_name]['new'](request)


# Register default question types
def register_default():
    from cs_questions.question_coding_io.views import QuestionViews
    register_question_type(models.io.CodingIoQuestion, 'io', QuestionViews)

register_default()
