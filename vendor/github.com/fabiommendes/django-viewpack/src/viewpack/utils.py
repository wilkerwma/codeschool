# Utility functions for the viewgroups module.
import re
import collections
from lazy import lazy

NOT_GIVEN = object()
REGEX_CACHE = collections.defaultdict(re.compile)


def get_app_name(cls):
    """Return the app_name associated with the given ViewPack class."""

    app_name = getattr(cls, 'app_name', None)

    if app_name is not None:
        return app_name

    return cls.__module__.partition('.')[0]


def get_pattern(obj, *, default=NOT_GIVEN):
        """
        Gets an url pattern string from method or view class.

        It first searches the `pattern` attribute. If not found, it uses the
        function or the class name. In both cases, it separates words by dashes
        rather than underscores or camel case and remove a trailing "-view", if
        it exists.
        """

        pattern = getattr(obj, 'pattern', None)

        if pattern is None:
            if default is NOT_GIVEN:
                name = get_view_name(obj, default=default)
                return '^%s/$' % name
            else:
                return default

        return pattern


def get_view_name(obj, *, default=NOT_GIVEN):
    """Return the view name for the given object."""

    view_name = getattr(obj, 'view_name', None)

    if view_name is None:
        if default is NOT_GIVEN:
            return get_url_name(obj).replace('-', '_')
        else:
            return default

    return view_name


def get_url_name(obj, *, default=NOT_GIVEN):
    """
    Return a suitable name attribute for reverse searches in for the given
    view object.
    """

    url_name = getattr(obj, 'url_name', None)

    if url_name is None:
        # Use the function/class name as name if no default is given
        if default is NOT_GIVEN:
            name = getattr(obj, '__name__', type(obj).__name__)
            name = camelcase_to_snakecase(name)
            name =  name.replace('_', '-')
            if name.endswith('-view'):
                name = name[:-5]
            return name
        else:
            return default

    return url_name


def parent_compose(obj, attr, unique=False):
    """Compose the given sequence attribute by joining the associated list of
    all parents."""

    out = []
    sequences = set()

    for link in obj.iter_parents(True):
        data = getattr(link, attr, None)
        data_id = id(data)
        if data and data_id not in sequences:
            sequences.add(data_id)
            if unique:
                data = [x for x in data if x not in out]
            out.extend(data)
    return out


def subclass_compose(obj, attr, unique=False):
    """Compose the given sequence attribute by joining the associated list of
    all base classes."""

    # This method accept instances or types. Let us normalize.
    if isinstance(obj, type):
        obj_type = obj
        out = []
        sequences = set()
    else:
        obj_type = type(obj)
        seq = getattr(obj, attr, [])
        out = list(seq)
        sequences = set(id(seq))

    # Search the mro for additional lists
    for link in obj_type.mro():
        data = getattr(link, attr, None)
        data_id = id(data)
        if data and data_id not in sequences:
            sequences.add(data_id)
            if unique:
                data = [x for x in data if x not in out]
            out.extend(data)
    return out


def camelcase_to_snakecase(name):
    """Convert a CamelCase name to snake_case."""
    if not name:
        return name

    letters = []
    prev = ''
    for letter in name:
        if letter.isupper() and not prev.isupper():
            letters.append('-')
        letters.append(letter.lower())

    underscore = ''.join(letters)
    return underscore[1:] if name[0].isupper() else underscore


def delegate_to_parent(attr, default=None):
    """
    Return a lazy descriptor that returns the value from the given property on
    parent or return the given default value.
    """

    @lazy
    def delegate_attribute(self):
        try:
            return getattr(self.parent, attr, default)
        except AttributeError:
            return default

    delegate_attribute.__name__ = attr
    return delegate_attribute
