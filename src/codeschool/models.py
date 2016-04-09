#
# Common classes and fields for all Codeschool apps.
#
# This module imports lots of third party fields and models classes and should
# be used as a droping replacement to django.db.models module.
#
# The database should not be touched here. This module should only host abstract
# models
#
import collections
from django.utils import timezone
from django.db.models import *
from django.db.models.fields.reverse_related import OneToOneRel as _OneToOneRel
from django.utils.translation import ugettext_lazy as _
from model_utils.models import *
from model_utils import Choices
from model_utils import managers as _mu_managers
from model_utils.managers import InheritanceManager as _InheritanceManager
from django.contrib.auth.models import *
from annoying.fields import JSONField, AutoOneToOneField
from picklefield.fields import PickledObjectField
from codeschool.utils import lazy


def _add_method(cls):
    def decorator(func):
        setattr(cls, func.__name__, func)
        return func
    return decorator


@_add_method(TimeFramedModel)
def reschedule(self, start, end=None, *, update=False):
    """Reschedule object to the given start and end times.

    It is necessary to .save() the object ir order to persist the changes in the
    database."""

    if end is None:
        end = start + (self.end - self.start)
    self.start = start
    self.end = end

    if update:
        self.save(update_fields=['start', 'end'])


@_add_method(TimeFramedModel)
def reschedule_now(self, minutes=None, *, update=False):
    """Reschedule the time framed object to span the interval from now and
    the given time span in minutes.

    It is necessary to .save() the object ir order to persist the changes in the
    database."""

    start = timezone.now()
    if minutes is not None:
        end = self.start + timezone.timedelta(minutes=minutes)
    else:
        end = None
    self.reschedule(start, end, update=update)


# Patch QueryManager to also be an InheritanceManager
_mu_managers.QueryManager.__bases__ = (_mu_managers.QueryManagerMixin,
                                       _mu_managers.InheritanceManagerMixin,
                                       Manager)


# Combinations of model_util models
class InheritableModel(models.Model):
    """A model with an InheritanceManager manager.

    When used with multiple inheritance, it generally should be the first base
    class.
    """

    class Meta:
        abstract = True

    objects = _InheritanceManager()

    @classmethod
    def get_subclasses(cls):
        """Return a list of all concrete subclasses."""

        classes = set()
        for field in cls._meta.related_objects:
            if isinstance(field, _OneToOneRel):
                rel_class = field.related_model
                if issubclass(rel_class, cls):
                    classes.add(rel_class)
                    for cls in rel_class.get_subclasses():
                        classes.add(cls)
        return list(classes)


class TimeFramedStatusModel(TimeFramedModel, StatusModel):
    """Mixin between TimeFramedModel and StatusModel"""

    class Meta:
        abstract = True

    expired = QueryManager()


class TimeStampedStatusModel(TimeStampedModel, StatusModel):
    """Mixin between TimeStampedModel and StatusModel"""
    class Meta:
        abstract = True


class TimeTrackingModel(TimeStampedModel, TimeFramedModel):
    """A model that is both TimeStamped and TimeFramed"""

    class Meta:
        abstract = True


class TimeTrackingStatusModel(TimeTrackingModel, StatusModel):
    """A TimeTrackingModel that has a status field."""

    class Meta:
        abstract = True


class DateFramedModel(models.Model):
    """Like a :cls:`TimeFramedModel`, but it's start and end fields are dates
    rather than datetimes."""

    class Meta:
        abstract = True

    start = DateField(_('start'), null=True, blank=True)
    end = DateField(_('start'), null=True, blank=True)


#
# Custom generic purpose models
#
ModelMeta = type(models.Model)
ListItemModel = None


class ListItemSequence(collections.MutableSequence):
    def __init__(self, owner, cls, accessor=None):
        if accessor is None:
            root_field = cls._meta.root_field
            field = cls._meta.get_field(root_field)
            accessor = field.remote_field.get_accessor_name()

        self._cls = cls
        self._owner = owner
        self._queryset = getattr(owner, accessor)

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
            raise NotImplementedError

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
    def __new__(cls, name, bases, ns):
        if ListItemModel is not None:
            try:
                meta = ns['Meta']
                root = getattr(meta, 'root_field')
                delattr(meta, 'root_field')
            except (KeyError, AttributeError):
                raise RuntimeError('you must define a Meta class with a '
                                   '"root_field" attribute')
            else:
                if not hasattr(meta, 'unique_together'):
                    meta.unique_together = ((root, 'index'),)
                else:
                    meta.unique_together = list(meta.unique_together)
                    meta.unique_together.append((root, 'index'))

            new = ModelMeta.__new__(cls, name, bases, ns)
            new._meta.root_field = root

            return new
        else:
            return ModelMeta.__new__(cls, name, bases, ns)


class ListItemModel(models.Model, metaclass=ListItemModelMeta):
    """
    An object that is an item in a list-like query set in the foreign key.

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

    >>> Container.items = Item.get_descriptor()

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
    def get_descriptor(cls):
        """Return a descriptor object that can be plugged into a container
        class in order to define a sequence interface to the related queryset.
        """

        @lazy
        def descr(self):
            return ListItemSequence(self, cls)
        return descr


# Implements codeschool.models.srvice.* namespace in which models from other
# sub-apps can be accessed from a sigle object
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

User.add_method = add_method
User.full_name = property(lambda s: '%s %s' % (s.first_name, s.last_name))
