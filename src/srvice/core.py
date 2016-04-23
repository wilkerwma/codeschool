"""
==============================================
Srvice: Javascript and Django working together
==============================================

The srvice framework corresponds of a small javascript library and a python
counterpart that makes javascript integrate well with django. The core
functionality is the ability to call python server-side functions and scripts
from client in a very transparent way.

All communication between the client and the server is done through JSON. The
client calls a server-side API as if it were a Javascript function and the
server may implement client-side behaviors in Python functions that are
transmitted back to the user and executed in Javascript. On top of this
functionality, srvice also implements some sugar.

How does it work?
=================

Srvice uses JSON to communicate between client and server. Even making some
"extensions" to JSON, this implies that there is a limitation in what kind of
objects can be transmitted from the client to the server and vice-versa. First
we extend JSON so all objects/dictionaries that have a "@type" key are handled
as some kind of specialized python or javascript object. For instance, datetime
objects are encoded as::

    {
        '@type': 'datetime',
        'data': 1232434342,      // number of seconds since Unix time
        'timezone': 120,         // number of minutes after UTC
    }

(In case you are curious, a dictionary with a '@type' key is encoded as
``{'@type': 'dict', 'data': {...whatever was in the dictionary...}}``).

Hence, the first step after the client makes a remote call to the server is to
encode all arguments using this scheme and wrap it in a structure like the one
bellow

::

    {
        'api': 'some-registered-server-side-function',
        'args': [arg1, arg2, arg3, ...],
        'kwargs': {
            'namedArg1': value1,
            'namedArg2': value2,
            ...
        },
        'action': 'api/program/js/html',
    }

This data is POST'ed into the server as JSON. The server should respond with
another JSON structure like this::

    {
        'result': <result from function call>,
        'program': [
            {'action': 'alert', 'message': 'hello world'},
            {'action': 'jqueryChain', 'selector': 'main', ...},
            ...
        ],
        'error': {
            'error': <error raised during server side execution>,
            'message': <error message>
            'traceback': <full python traceback (only if DEBUG=True)>
        }
    }

The first part to be processed is the "critical" key. If present, it encodes
any internal error that has occurred in the process of calling the server-side
function (but not errors raised by the function). These errors can be:

1. Invalid method used in HTTP request. In most cases, srvice expect POST
   requests.
2. Could not decode input arguments or the resulting value to JSON.
3. The user is not allowed to call the given method.
4. The input parameters do not match the function signature.
5. Invalid API function name.

In Javascript, any of theses errors throw a ??Error, with a `message` attribute
explaining the reason of the error and a numeric `code` attribute with the
number given in parenthesis.

If the server-side function raises an error (with the exception of
PermissionError's, which are always considered to be critical), the error
is encoded in the "error" key. These errors are also re-raised (or thrown) in
javascript, but as a generic Error() class. If Django is running in debug mode,
it also prepends a string with the full Python traceback before the error
message.

These errors are actually processed **after** the "program" part of the
response. The program is a sequence of instructions to be executed in the
client as if it were a javascript function. The srvice.js library can handle
several instructions, which are documented in ???. In the server, these
instructions are codified in the :class:`srvice.Client`.

Finally, the "result" key stores the JSON-encoded return value for the function.


Model query
===========

With srvice, javascript can query and modify registered models in the database.
For obvious security reasons, we do not expose any model by default, but rather,
the user must register explicitly each model that can be transmitted or modified
by the client. This process allows one to specify explicitly which fields
should be available to each user.

**Under construction.**

"""

import io
import inspect
import functools
import traceback
from json import loads
from django import http
from django.core import exceptions
from django.views.generic import View
from django.views.decorators.csrf import csrf_exempt
from srvice import json
from srvice.client import Client

rpc_namespace = {}
rpc_safe_namespace = {}
DEBUG = True


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
        if apiname not in SrviceView.registry:
            raise http.Http404(rpc_namespace)
        method = SrviceView.registry[apiname]
    else:
        return method(request)


class BadResponseError(Exception):
    """Exception raised when an srvice API would return an error response
    object."""

    def __init__(self, *args, **kwds):
        super().__init__(args)
        for (k, v) in kwds.items():
            setattr(self, k, v)

    @property
    def response(self):
        for arg in self.args:
            if isinstance(arg, http.HttpResponse):
                return arg
        else:
            return http.HttpResponseServerError()


class SrviceView(View):
    """
    Wraps a srvice API/Program/etc into a view.

    Users should more conveniently use the :func:`srvice.program` or
    :func:`srvice.api decorators`.


    Args:
        function:
            (required) The function handle that implements the given API.
        login_required:
            If True, the API will only be available to logged in users.
        perms_required:
            The list of permissions a user must have in order to use the API.
    """

    # Class constants and attributes
    valid_content_types = {
        'application/json',
        'application/javascript',
        'text/x-json'
    }

    # Constructor
    def __init__(self, function, action='api', login_required=False,
                 perms_required=None, **kwds):
        self.function = function
        self.action = action
        self.login_required = login_required
        self.perms_required = perms_required
        super().__init__(**kwds)

    def get_data(self, request):
        """
        Decode and return data sent from the client.
        """

        try:
            payload = json.loads(request.body)
        except Exception as ex:
            raise BadResponseError(http.HttpResponseServerError(ex))
        return payload

    def process_data(self, request, data):
        """Execute the API function and return a dictionary with the results."""

        error = result = program = None
        args = data.get('args', ()),
        kwargs = data.get('kwargs', {})
        out = {}

        try:
            out.update(self.execute(request, *args, **kwargs))
        except Exception as ex:
            out['error'] = self.wrap_error(ex, ex.__traceback__)

        return out

    def wrap_error(self, ex, tb=None, wrap_permission_errors=False):
        """Wraps an exception raised during the execution of an API function."""

        if not wrap_permission_errors and isinstance(ex, PermissionError):
            response = http.HttpResponseForbidden(ex)
            raise BadResponseError(response)

        error = {
            'error': type(ex).__name__,
            'message': str(ex)
        }
        if DEBUG:
            file = io.StringIO()
            traceback.print_tb(tb or ex.__traceback__, file=file)
            error['traceback'] = file.getvalue()
        return error

    def execute(self, request, *args, **kwargs):
        """Execute API action.

        Any exceptions are wrapped into an error dictionary and sent back in
        the final response."""

        return {'result': self.function(request, *args, **kwargs)}

    def check_credentials(self, request):
        """Assure that user has the correct credentials to the process.

        Must raise a BadResponseError if credentials are not valid."""

        if self.login_required or self.perms_required:
            if request.user is None:
                response =  http.HttpResponseForbidden('login required')
                raise BadResponseError(response)
        if self.perms_required:
            user = request.user
            for perm in self.perms_required:
                if not user.has_perm(perm):
                    msg = 'user does not have permission: %s' % perm
                    response = http.HttpResponseForbidden(msg)
                    raise BadResponseError(response)
        # TODO: check csrf token

    def get_payload(self, data):
        """Return the payload that will be sent back to the client.

        The default implementation simply converts data to JSON."""

        result = data.get('result')
        program = data.get('program')
        error = data.get('error')

        # Encode result value
        if result is not None:
            try:
                result = json.dumps(result)
            except Exception as ex:
                response = http.HttpResponseServerError(ex)
                raise BadResponseError(response)
        if program is not None:
            try:
                program = json.dumps(program)
            except Exception as ex:
                response = http.HttpResponseServerError(ex)
                raise BadResponseError(response)
        if error is not None:
            try:
                error = json.dumps(error)
            except Exception as ex:
                response = http.HttpResponseServerError(ex)
                raise BadResponseError(response)

        # Manually construct the JSON payload
        payload = ['{']
        if result:
            payload.append('"result":%s,' % result)
        if program:
            payload.append('"program":%s,' % program)
        if error:
            payload.append('"error":%s,' % error)
        if payload[-1].endswith(','):
            payload[-1] = payload[-1][:-1]
        payload.append('}')
        payload = ''.join(payload)
        return payload

    def get_content_type(self):
        """Content type of the resulting message.

        For JSON, it returns 'application/json'."""

        return 'application/json'

    def get(self, request):
        """Process the given request, call handler and return result."""

        try:
            self.check_credentials(request)
            data = self.get_data(request)
            out = self.process_data(request, data)
            payload = self.get_payload(out)
            content_type = self.get_content_type()
        except BadResponseError as ex:
            return ex.response

        return http.HttpResponse(payload, content_type=content_type)


class SrviceAPIView(SrviceView):
    """
    View to functions registered with the @api decorator.
    """


class SrviceProgramView(SrviceView):
    """
    View to functions registered with the @program decorator.
    """

    def execute(self, request, *args, **kwargs):
        out = {}
        client = Client(request)
        try:
            out['result'] = self.function(client, *args, **kwargs)
        except Exception as ex:
            out['error'] = self.wrap_error(ex, ex.__traceback__)
        out['program'] = client.compile()
        return out


def SrviceJsView(SrviceView):
    """
    View to functions registered with the @js decorator.
    """


def SrviceHtmlView(SrviceAPIView):
    """
    View to functions registered with the @html decorator.
    """


def api(*args, name=None, **kwargs):
    """
    Register a remote procedure call API function .

    This function can be used as a decorator or as a regular function call::

        @srvice.api('server-fib')
        def fib(request, n):
            if n <= 1:
                return 1
            else:
                return fib(n - 1) + fib(n - 2)

        srvice.api(fib, name='server-fibonacci')

    Keyword Args:
        name:
            Name of the API entry point. By default, srvice uses the a
            "app-label.func-name" convention, in which the "app-label"
            corresponds to the root level of the module path in which the
            function was defined and "func-name" is the Python function name.
            In both strings, underscores are replaced by dashes.
        login_required:
            If True (default is False), the API will only work if the user is
            logged-in.
        perm_required:
            A list of required permissions that a logged in user must have in
            order to access the API.
    """

    return srvice_register(SrviceAPIView, *args, name=name)


def program(*args, name=None, **kwargs):
    """
    Register a program API.

    This function can be used as a decorator or as a regular function call::

        @srvice.program('server-fat')
        def fat(client, n):
            result = 1
            for i in range(1, n + 1):
                result *= i
            client.alert('Factorial of %s = %s' % (n, result))
            return result

        srvice.program(fat, name='server-fibonacci')
    """

    return srvice_register(SrviceProgramView, *args, name=name)


def srvice_register(view_cls, *args, name=None, register=True, **kwargs):
    """
    Worker function for api and program callbacks.
    """

    # Decorator form
    if not args or isinstance(args[0], str):
        if args:
            name, *args = args

        def decorator(func):
            srvice_register(view_cls, func, *args, name=name)
            return func
        return decorator

    # Register SrviceView
    if len(args) == 2:
        if name is None:
            name, *args = args
        else:
            raise TypeError('function expect a single positional argument')
    if len(args) != 1:
        raise TypeError('invalid number of positional arguments')

    # Compute the default name, if not given
    func = args[0]

    if name is None:
        func_name = func.__qualname__
        mod_name = func.__module__
        name = ('%s.%s' % (func_name, mod_name)).replace('_', '-')

    # Create view and register
    view = view_cls.as_view(func, name=name, **kwargs)

    if register:
        if name in __srvice_registry__:
            raise ValueError('api %r already exists' % name)
        __srvice_registry__[name] = view
    return view

__srvice_registry__ = {}
