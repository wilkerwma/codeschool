
class JQueryWrapper:
    """Implements jQuery-like chained calls in the Client rpc interface."""

    def __init__(self, context, selector):
        self.context = context
        self.selector = selector

    def __getattr__(self, attr):
        def func(*args, **kwds):
            if kwds:
                args += (kwds,)
            self.context.action('jquery-exec',
                                func=attr,
                                selector=self.selector,
                                args=list(args))
            return self
        return func


class Client:
    """Represents an RPC session with a client."""

    def __init__(self, request):
        self._statements = []
        self.result = None
        self.request = request

    def __call__(self, selector):
        return JQueryWrapper(self, selector)

    def as_json_result(self):
        """Convert RPC object to a JSON-encodable structure."""

        json = {"result": self.result}
        if len(self._statements) == 1:
            json["exec"] = self._statements[0]
        else:
            json["exec"] = {"action": "statements", "data": self._statements}
        return json

    # noinspection PyMethodParameters
    def action(__self, action=None, **kwargs):
        # Calls a registered RPC action. We renamed self in order to be able to
        # pass self again in kwargs, ignoring it later.
        if kwargs.get('self', None) is __self:
            del kwargs['self']
        self = __self

        if 'kwargs' in kwargs:
            new_args = kwargs
            kwargs = kwargs.pop('kwargs')
            kwargs.update(new_args)

        if action is not None:
            kwargs['action'] = action

        self._statements.append(kwargs)

    # Return values
    def value(self, value):
        """Sets the return attribute and return itself.

        This function is used in the following idiom::

            @srvice
            def double(x):
                js = Client()
                js.alert('x = %s, 2x = %s' % (x, 2 * x))
                return js.value(2 * x)
        """

        self.result = value
        return self

    def error(self, exception, message="server-side error"):
        """Function is used to raise an error in the client after executing
        some functions::

            @srvice
            def sqrt(x):
                value = math.sqrt(x) if x >=0 else None

                js = Client()
                if value is not None:
                    return js.value(math.sqrt(x))
                else:
                    return js.error(ValueError, 'cannot compute square root of '
                                                'a negative number')
        """

        json = self.as_json_result()
        json['error'] = {
            'error': exception.__name__,
            'error-message': message,
        }
        del json['result']

    # Functions and commands that the client-side srvice object understand
    def alert(self, st):
        """Show an alert window on client."""

        self.action('alert', data=st)

    def redirect(self, url, as_link=False):
        """Redirect to the given url.

        If ``as_link=True``, make a redirect as if the user had clicked on a
        link. Otherwise, make a new http request."""

        self.action('redirect', **locals())

    def eval(self, source):
        """Evaluate string of javascript source."""

        self.action('eval', data=source)

    def html(self, source, element=None):
        """Replace html code of the given element or JQueryWrapper selection.

        If no element is given, uses the element which called the function."""

        self.action('html', selector=element, data=source)

    def __getattr__(self, attr):
        def func(**kwds):
            self.action(attr, **kwds)
        return func
