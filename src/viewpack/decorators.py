from viewpack.utils import get_pattern, get_url_name, get_view_name


def view(*args, pattern=None, name=None, view_name=None, url_name=None):
    """Decorator that marks some method as a view function.

    It saves the following attributes to the decorated method:

    is_view:
        This is always True
    pattern:
        A string with a Django url pattern. The default is to match the method
        name with underscores replaced by dashes.
    url_name:
        The name suffix for the url associated with this view. The url can be
        reversed as reverse('<viewgroup-name>-<view-name>', *args, **kwargs).
        This attribute is aliased as 'name'.
    view_name:
        Name of the view that is used in ViewPack.as_view(<view name>). By
        default it is just the url_name with dashes replaced by underscores.
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
            view(func, pattern=pattern, name=name)
            return func
        return decorator

    # Register attributes to function
    if pattern is None:
        pattern = get_pattern(func)
    if url_name is None and name is None:
        url_name = get_url_name(func)
    if url_name is None:
        url_name = name
    if view_name is None:
        view_name = get_view_name(func)

    func.is_view = True
    func.pattern = pattern
    func.url_name = url_name
    func.view_name = view_name
