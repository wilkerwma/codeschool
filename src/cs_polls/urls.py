from django.conf.urls import url
from cs_polls import views
from django.http import HttpResponse, JsonResponse


from django.views.decorators.csrf import csrf_exempt
from functools import wraps
from collections import Mapping


def json_function(function):
    """
    Decorator that marks a function that return a dictionary of JSON-compatible
    data in a view function that emits JsonResponse objects.

    Example:

        @json_function
        def func(request):
            return {'foo': 1, 'bar': 42}

    """

    @wraps(function)
    @csrf_exempt
    def decorated(request, *args, **kwargs):
        obj = function(request, *args, **kwargs)
        if not isinstance(obj, Mapping):
            raise TypeError('your JSON function must return a dictionary')
        return JsonResponse(obj)

    return decorated


@json_function
def stats_view(request, pk):
    """Return a dictionary with the number of votes for each alternative."""

    from codeschool.dbg import console
    console()

    return {'d': request.GET}


urlpatterns = [
    url('^(?P<pk>\d+)/stats/$', stats_view),
    url('^', views.PollCRUD.as_include(namespace='poll')),
]
