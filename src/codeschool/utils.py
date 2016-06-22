"""
Like codeschool.shortcuts for things that do not touch the database or any
django-related settings.
"""
import hashlib
from functools import partial
import pprint


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
        self.__name__ = getattr(method, '__name__', None)

    def __get__(self, obj, cls):
        if obj is None:
            return self

        result = self.method(obj)
        try:
            attr_name = self._attr
        except AttributeError:
            attr_name = self.get_attribute_name(cls)

        setattr(obj, attr_name, result)
        return result

    def get_attribute_name(self, cls):
        """Inspect live object for some attributes."""

        try:
            if getattr(cls, self.__name__) is self:
                return self.__name__
        except AttributeError:
            pass

        for attr in dir(cls):
            method = getattr(cls, attr, None)
            if method is self:
                self._attr = attr
                return attr

        raise TypeError('lazy accessor not found in %s' % cls.__name__)


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


def migrate_object(obj, cls, blacklist=(), save=False,
                   kwargs_T=lambda x, y: y, new_T=lambda x: x, verbose=True):
    """Create instance from cls using data from the given object."""

    kwargs = {}
    for field in obj._meta.fields:
        field = field.name
        kwargs[field] = getattr(obj, field)
    kwargs = kwargs_T(obj, kwargs)
    new = new_T(cls(**kwargs))

    if save:
        new.save()
    if verbose:
        print('*' * 60)
        print('new %s:' % cls.__name__)
        pprint.pprint(kwargs)
    return new


def migrate_all(clsA, clsB, base='base', **kwargs):
    """
    Migrate all objects from clsA to clsB
    """

    bases = clsB.objects.values_list(base, flat=True)
    for obj in clsA.objects.all().exclude(id__in=bases):
        migrate_object(obj, clsB, **kwargs)


class delegate_to:
    """Creates a simple delegation property."""

    def __init__(self, delegate_to, readonly=False):
        self.delegate_to = delegate_to
        self.readonly = readonly

    def __get__(self, obj, cls=None):
        if obj is None:
            return self
        owner = getattr(obj, self.delegate_to)
        try:
            attr = self._name
        except AttributeError:
            attr = self._get_name(cls)
        return getattr(owner, attr)

    def __set__(self, obj, value):
        if self.readonly:
            raise AttributeError

        owner = getattr(obj, self.delegate_to)
        try:
            attr = self._name
        except AttributeError:
            attr = self._get_name(type(cls))
        setattr(owner, attr, value)

    def _get_name(self, cls):
        for k in dir(cls):
            v = getattr(cls, k)
            if v is self:
                return k
        raise RuntimeError('not a member of class')


if __name__ == '__main__':
    import doctest
    doctest.testmod()


def md5hash(st):
    """Compute the hex-md5 hash of string.

    Returns a string of 32 ascii characters."""

    return hashlib.md5(st.encode('utf8')).hexdigest()