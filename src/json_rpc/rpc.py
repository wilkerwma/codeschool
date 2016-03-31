import inspect
import functools
from json import loads, dumps
from django import http
from django.conf.urls import url


rpc_namespace = {}
rpc_safe_namespace = {}


def remote_call(*args, method='POST'):
    """
    Marks a view method that process JSON remote procedure calls.
    """

    if not args:
        def decorator(func):
            return remote_call(func, method=method)
        return decorator

    func, = args
    spec = inspect.getfullargspec(func)

    # API name
    qualname = func.__module__ + '.' + func.__name__
    qualname = qualname.replace('.views.', '')

    # Annotated types
    types = spec.annotations
    types.pop('return', None)

    # Required keywords
    required = spec.args[:]
    for _ in spec.defaults:
        required.pop()
    required = set(required)

    # JSON content types
    valid_content_types = {
        'application/json',
        'application/javascript',
        'text/x-json'
    }

    @functools.wraps(func)
    def callback(request):
        # Only accept the correct http method
        if request.method != method:
            msg = 'invalid http method: %s' % method
            return http.HttpResponseBadRequest(msg)

        # Check content
        try:
            json = loads(request.body)
        except Exception as ex:
            request.content_type = 'broken json (%s)' % ex
        if request.content_type not in valid_content_types:
            msg = 'invalid content: %s' % method
            return http.HttpResponseBadRequest(msg)

        # Checks if all arguments were passed
        if not required.issubset(json):
            missing = required.difference(json)
            msg = 'missing arguments: %s' % list(missing)
            return http.HttpResponseBadRequest(msg)

        # Check types
        if not all(isinstance(json[k], tt) for (k, tt) in types.items()):
            error = {k for (k, tt) in types.items()
                       if not isinstance(json[k], tt)}
            msg = 'invalid types: %s' % list(error)
            return http.HttpResponseBadRequest(msg)

        result = func(**json)
        json_response = dumps(result)
        return http.HttpResponse(json_response,
                                 content_type='application/json',
                                 charset='utf8')

    # Register view function
    rpc_namespace[qualname] = callback
    return func


def dispatch_view(request, apiname):
    """Dispatch request to the correct rpc function."""

    try:
        method = rpc_namespace[apiname]
    except KeyError:
        return http.Http404
    else:
        return method(request)


urlpatterns = [
    url(r'^(.*)$', dispatch_view, name='json-rpc'),
]