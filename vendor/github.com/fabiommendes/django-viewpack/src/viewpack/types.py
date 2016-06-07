from viewpack.utils import lazy


class DetailObject:
    """
    Exposes object with a normalized interface that can be conveniently
    used in      generic templates.
    """

    def __init__(self, view):
        self._view = view

    def __getattr__(self, attr):
        return getattr(self.object, attr)

    @lazy
    def object(self):
        return self._view.object

    @lazy
    def title(self):
        try:
            return self.object.title
        except AttributeError:
            return getattr(self.object, 'name', self.object)

    @lazy
    def short_description(self):
        try:
            return self.object.short_description
        except AttributeError:
            if hasattr(self.object, 'long_description'):
                return getattr(self.object, 'description', None)

    @lazy
    def long_description(self):
        try:
            return self.object.long_description
        except AttributeError:
            return getattr(self.object, 'description', None)

    @lazy
    def description_list(self):
        # Fetch fields
        fields = getattr(self._view, 'detail_fields', None)
        if fields is None:
            fields = getattr(self._view, 'fields', None)
        if fields is None:
            return []

        # Return list with field values
        out = []
        obj = self.object
        blacklist = {'title', 'name',
                     'description', 'short_description', 'long_description'}

        for field in fields:
            if field not in blacklist:
                data = getattr(obj, field, None)
                field = obj._meta.get_field(field)
                label = str(field.verbose_name).title()
                out.append((label, data))

        return out


class LazyBool:
    """
    Lazy boolean-like value.
    """

    def __init__(self, callable):
        self.callable = callable

    @lazy
    def value(self):
        return self.callable()

    def __bool__(self):
        return bool(self.value)

    def __add__(self, other):
        return self.value.__add__(other)

    def __radd__(self, other):
        return self.value.__radd__(other)

    def __sub__(self, other):
        return self.value.__sub__(other)

    def __rsub__(self, other):
        return self.value.__rsub__(other)

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return repr(self.value)
