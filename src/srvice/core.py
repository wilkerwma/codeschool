import inspect
import functools
from json import loads
from django import http
from django.views.decorators.csrf import csrf_exempt
from srvice.client import Client

rpc_namespace = {}
rpc_safe_namespace = {}


def srvice(*args, method='POST'):
    """
    Marks a view method that process JSON remote procedure calls.
    """

    if not args:
        def decorator(function):
            return srvice(function, method=method)
        return decorator

    func, = args
    spec = inspect.getfullargspec(func)

    # API name
    qualname = func.__module__ + '.' + func.__name__
    qualname = qualname.replace('.views.', '.').replace('_', '-')

    # Annotated types
    types = spec.annotations
    types.pop('return', None)

    # Required keywords
    required = spec.args[:]
    for _ in (spec.defaults or []):
        required.pop()
    required = set(required)
    request_required = spec and (spec.args[0] == 'request')

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
            json = loads(request.body.decode('utf8'))
            if request_required:
                json['request'] = request
        except Exception as ex:
            return http.HttpResponseBadRequest('invalid JSON data: %s' % ex)

        content_type = request.META.get('CONTENT_TYPE')
        if content_type not in valid_content_types:
            msg = 'invalid content type: %s' % content_type
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

        # Prepare response
        try:
            result = func(**json)
        except Exception as ex:
            result = {'error-message': str(ex),
                      'error': type(ex).__name__}
        else:
            if isinstance(result, Client):
                result = result.as_json_result()
            else:
                result = {"result": result}
        print(result)
        return http.JsonResponse(result)

    # Register view function
    rpc_namespace[qualname] = callback
    print(qualname)
    return func


@csrf_exempt
def dispatch_view(request, apiname):
    """Dispatch request to the correct srvice function."""

    try:
        method = rpc_namespace[apiname]
    except KeyError:
        raise http.Http404(rpc_namespace)
    else:
        return method(request)

