from functools import partial, wraps
from viewpack.utils import get_pattern, get_url_name, get_view_name
__all__ = ['view', 'api', 'program', 'js', 'html']
view_arg_names = {'pattern', 'view_name', 'url_name'}


def view(*args, pattern=None, view_name=None, url_name=None):
    r"""Decorator that marks some method as a view function.

    This function accept the following keyword arguments that are saved in the
    decorated method.

    Args:
        pattern:
            A string with a Django url pattern. The default is to match the
            method name with underscores replaced by dashes.
        url_name:
            The name suffix for the url associated with this view. The url can
            be reversed as reverse('<viewgroup-name>-<view-name>', *args, **kwargs).
            This attribute is aliased as 'name'.
        view_name:
            Name of the view that is used in ViewPack.as_view(<view name>). By
            default it is just the url_name with dashes replaced by underscores.

    Usage::

        from viewpack import ViewPack, view
        from django import http

        class MyPack(ViewPack):

            @view(pattern=r'^fib:(?P<N>\d+)$')
            def fib(request, N):
                '''A page with a simple list of Fibonacci numbers.'''

                L = [1, 1]
                while len(L) < N:
                    L.append(L[-1] + L[-2])
                return http.HttpResponse('fib: %s' % L[:N])

    In the above example, MyPack register a view method to the given sub-url
    pattern.

    """
    if not args:
        func = None
    elif len(args) == 1:
        func, = args
        if pattern is None and isinstance(func, str):
            func, pattern = None, func
    else:
        raise TypeError('expects at most a single positional argument')

    # Since func is None, we are using the decorator form of the view function
    # Let us return the decorator
    if func is None:
        def decorator(func):
            return view(
                func, pattern=pattern, url_name=url_name, view_name=view_name
            )
        return decorator

    # Register attributes to function
    if pattern is None:
        pattern = get_pattern(func)
    if url_name is None:
        url_name = get_url_name(func)
    if view_name is None:
        view_name = get_view_name(func)

    func.is_view = True
    func.pattern = pattern
    func.url_name = url_name
    func.view_name = view_name
    return func


def api(*args, **kwargs):
    r"""
    Marks the ViewPack method as a srvice api view.

    This function accepts both the arguments from :func:`viewpack.view`
    or :func:`srvice.api` decorators.

    Usage::

        from viewpack import ViewPack, api

        class MyPack(ViewPack):

            @api(pattern=r'^fib$')
            def fib(request, N):
                '''Compute a list of Fibonacci numbers.'''

                L = [1, 1]
                while len(L) < N:
                    L.append(L[-1] + L[-2])
                return L[:N]
    """

    import srvice
    return srvice_decorator(srvice.api)(*args, **kwargs)


def program(*args, **kwargs):
    """
    Marks the ViewPack method as a srvice program view.

    This function accepts both the arguments from :func:`viewpack.view`
    or :func:`srvice.program` decorators.
    """

    import srvice
    return srvice_decorator(srvice.program)(*args, **kwargs)


def js(*args, **kwargs):
    """
    Marks the ViewPack method as a srvice js view.

    This function accepts both the arguments from :func:`viewpack.view`
    or :func:`srvice.js` decorators.
    """

    import srvice
    return srvice_decorator(srvice.js)(*args, **kwargs)


def html(*args, **kwargs):
    """
    Marks the ViewPack method as a srvice html view.

    This function accepts both the arguments from :func:`viewpack.view`
    or :func:`srvice.html` decorators.
    """

    import srvice
    return srvice_decorator(srvice.html)(*args, **kwargs)


def srvice_decorator(srvice_func):
    """
    Worker function for all srvice based decorators
    """

    def decorator(*args, **kwargs):
        # Separate arguments destined to the view() decorator and to the
        # srvice decorator
        view_kwargs = {
            k: kwargs.get(k) for k in view_arg_names
        }
        srvice_kwargs = {
            k: v for (k, v) in kwargs.items() if k not in view_kwargs
        }

        # Decorator form of the method
        if not args:
            return lambda f: decorator(f, **kwargs)

        func, = args
        func = view(**view_kwargs)(func)

        # Update the as_view function that srvice creates to save the ViewPack
        # parameters to the decorated function and to make it work as a method
        def as_view():

            @wraps(func)
            def decorated(self, request, *args, **kwargs):
                method = srvice_func(**srvice_kwargs)(partial(func, self))
                view_func = method.as_view()
                return view_func(request, *args, **kwargs)

            decorated.view_name = func.view_name
            decorated.pattern = func.pattern
            decorated.url_name = func.url_name
            return decorated

        func.as_view = as_view
        return func

    return decorator
