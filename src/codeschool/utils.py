"""
Like codeschool.shortcuts for things that do not touch the database or any
django-related settings.
"""
from functools import partial


class lazy:
    """Define a lazy property.

    Examaple
    --------

    >>> class Foo:
    ...     @lazy
    ...     def bar(self):
    ...         print('the answer')
    ...         return 42  # ... after a long computation


    We can use the lazy property just as any attribute that has a default value.

    >>> x = Foo()
    >>> x.bar = 40
    >>> x.bar
    40
    >>> y = Foo()
    >>> y.bar
    the answer
    42
    """

    def __init__(self, method):
        self.method = method
        self._attr = None

    def __get__(self, obj, cls=None):
        if obj is not None:
            result = self.method(obj)
            setattr(obj, self.attr(obj), result)
            return result

    def attr(self, obj):
        if self._attr is not None:
            return self._attr

        for attr, method in vars(type(obj)).items():
            if method is self:
                self._attr = attr
                return attr

        raise TypeError('lazy accessor not found in %s' % type(obj).__name__)


def delegation(delegate_attr, fields):
    """Decorator that register automatic property-based delegations for the
    given class

    Example
    -------

        @delegation('data', ['upper', 'lower'])
        class Foo:
            def __init__(self, data):
                self.data = data

    In the example, the attributes Foo.upper and Foo.lower automatically created
    to be properties that return the corresponding attributes from Foo.data.
    """
    def delegate(field_name, self):
        source = getattr(self, delegate_attr)
        return getattr(source, field_name)

    def decorator(cls):
        for field in fields:
            prop = property(partial(delegate, field))
            setattr(cls, field, prop)
        return cls

    return decorator

if __name__ == '__main__':
    import doctest
    doctest.testmod()