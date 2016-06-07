import collections
from lazy import lazy
from django.db import models
from django.core.exceptions import ImproperlyConfigured


__all__ = ['ListItemModel', 'ListItemSequence']
ModelMeta = type(models.Model)


class ListItemSequence(collections.MutableSequence):
    """
    Descriptor object that exposes the related items of a ListItemModel as a
    sequence interface.

    This descriptor should be used as a class attribute as in the example::

        class Item(ListItemModel):
            class Meta:
                root_field = 'container'

            container = models.ForeignKey('Container')


        class Container(models.Model):
            items = ListItemSequence.as_item(Item)

    """
    def __init__(self, owner, cls, accessor=None):
        if accessor is None:
            root_field = cls._meta.root_field
            field = cls._meta.get_field(root_field)
            accessor = field.remote_field.get_accessor_name()

        self._cls = cls
        self._owner = owner
        self._queryset = getattr(owner, accessor)

    @classmethod
    def as_items(cls, item_class):
        """Return a descriptor object that exposes a group of ListItemModel
        items as a Python sequence object."""

        @lazy
        def descriptor(self):
            return cls(self, item_class)
        return descriptor

    def _check(self, value):
        if not isinstance(value, self._cls):
            tname = self._cls.__name__
            raise TypeError('expect %s instances, got %r' % (tname, value))

    def _norm_int_idx(self, idx):
        size = len(self)
        if idx < 0:
            idx += size
            if idx < 0:
                raise IndexError(idx - size)
        if idx >= size:
            raise IndexError(idx)
        return idx

    def __iter__(self):
        return iter(self._queryset.order_by('index').all())

    def __len__(self):
        return self._queryset.count()

    def __setitem__(self, idx, value):
        self._check(value)
        idx = self._norm_int_idx(idx)
        self[idx].delete()
        value.index = idx
        value._root = self._owner
        value.save()

    def __getitem__(self, idx):
        if isinstance(idx, int):
            idx = self._norm_int_idx(idx)
            return self._queryset.get(index=idx)
        else:
            raise KeyError(idx)

    def __delitem__(self, idx):
        self[idx].delete()

    def insert(self, idx, value):
        self._check(value)
        idx = self._norm_int_idx(idx)

        for item in self._queryset.filter(index__gte=idx).order_by('-index'):
            item.index += 1
            item.save(update_fields=['index'])

        value.index = idx
        value._root = self._owner
        value.save()

    def append(self, value):
        self._check(value)

        value.index = len(self)
        value._root = self._owner
        value.save()

    def fix_indexes(self):
        """Fix all indexes."""

        for idx, item in enumerate(self):
            if item.index != idx:
                item.index = idx
                item.save(update_fields=['index'])


class ListItemModelMeta(ModelMeta):
    """
    Metaclass for ListItemModel classes.
    """
    def __new__(cls, name, bases, ns):
        try:
            meta = ns['Meta']
            root = getattr(meta, 'root_field')
            delattr(meta, 'root_field')
        except (KeyError, AttributeError):
            if 'ListItemModel' not in globals():
                return ModelMeta.__new__(cls, name, bases, ns)

            raise ImproperlyConfigured(
                'class must define a Meta class with a "root_field" '
                'attribute with the name of the foreign key main reference')
        else:
            if not hasattr(meta, 'unique_together'):
                meta.unique_together = ((root, 'index'),)
            else:
                meta.unique_together = list(meta.unique_together)
                meta.unique_together.append((root, 'index'))

            new = ModelMeta.__new__(cls, name, bases, ns)
            new._meta.root_field = root
            return new


class ListItemModel(models.Model, metaclass=ListItemModelMeta):
    """
    An object that is an item for a list-like object related by a foreign key.

    Subclasses must implement a Meta inner class that defines the ``root_field``
    attribute.

    Example
    -------

    First we define the container class model. It has no reference for the
    list.

    >>> class Container(models.Model):
    ...     name = models.CharField(max_length=100)
    ...     ...

    Now we add the ListItemModel

    >>> class Item(ListItemModel):
    ...     root = models.ForeignKey(Container)
    ...
    ...     class Meta:
    ...         root_field = 'root'

    Finally, we patch Container object to have a sequence-like object interface
    to its ListItemModel children

    >>> Container.items = ListItemSequence.as_items(Item)

    Now we can manipulate the items attribute of Container objects essencially
    as a list of objects.
    """

    index = models.PositiveIntegerField()

    class Meta:
        abstract = True

    @property
    def _root(self):
        return getattr(self, self._meta.root_field)

    @_root.setter
    def _root(self, value):
        setattr(self, self._meta.root_field, value)

    @property
    def _siblings(self):
        root_field = self._meta.get_field(self._meta.root_field)
        related_name = root_field.remote_field.get_accessor_name()
        return getattr(self._root, related_name)

    def save(self, *args, **kwds):
        if self.index is None:
            siblings = self._siblings
            if siblings:
                self.index = siblings.count()
            else:
                self.index = 0
        super().save(*args, **kwds)

    def delete(self, *args, **kwds):
        siblings = self._siblings
        super().delete(*args, **kwds)

        for idx, item in enumerate(siblings.order_by('index')):
            if item.index != idx:
                item.index = idx
                item.save(update_fields=['index'])

    def next(self, skip=1):
        """Return the next siblings (or the one skiping skip positions)."""

        try:
            return self._siblings.get(index=self.index + skip)
        except self.DoesNotExist:
            return None

    def prev(self, skip=1):
        """Like next(), but goes backwards."""

        return self.next(-skip)

    @classmethod
    def as_items(cls):
        """Return a descriptor object that can be plugged into a container
        class in order to define a sequence interface to the related queryset.
        """

        return ListItemSequence.as_items(cls)


# Implements codeschool.models.srvice.* namespace in which models from other
# sub-apps can be accessed from a single object
class _CsSingletonType:
    """A simple namespace to access models from other cs_* apps"""

    def __getattr__(self, attr):
        try:
            value = __import__('cs_%s.models' % attr)
        except ImportError:
            raise AttributeError(attr)
        setattr(self, attr, value)
        return value

cs = _CsSingletonType()


# Monkey patch python-level behavior of the User object
def add_method(func):
    """Decorator that adds a new method to class.

    Raise a runtime error if method exists."""

    if hasattr(User, func.__name__):
        raise RuntimeError('cannot add method %s to class User: method exists!'
                           % func.__name__)
    setattr(User, func.__name__, func)
    return func
