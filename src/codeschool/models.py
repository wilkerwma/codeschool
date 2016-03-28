#
# Common classes and fields for all Codeschool apps.
#
# This module imports lots of third party fields and models classes and should
# be used as a droping replacement to django.db.models module.
#
# The database should not be touched here. This module should only host abstract
# models
#
from django.utils import timezone
from django.db.models import *
from django.db.models.fields.reverse_related import OneToOneRel as _OneToOneRel
from model_utils.models import *
from model_utils import Choices
from model_utils import managers as _mu_managers
from model_utils.managers import InheritanceManager as _InheritanceManager
from django.contrib.auth.models import *
from annoying.fields import JSONField, AutoOneToOneField
from picklefield.fields import PickledObjectField


def _add_method(cls):
    def decorator(func):
        setattr(cls, func.__name__, func)
        return func
    return decorator


@_add_method(TimeFramedModel)
def reschedule(self, start, end):
    """Reschedule object to the given start and end times.

    It is necessary to .save() the object ir order to persist the changes in the
    database."""

    self.start = start
    self.end = end


@_add_method(TimeFramedModel)
def reschedule_now(self, minutes):
    """Reschedule the time framed object to span the interval from now and
    the given time span in minutes.

    It is necessary to .save() the object ir order to persist the changes in the
    database."""

    self.start = timezone.now()
    self.end = self.start + timezone.timedelta(minutes=minutes)


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


# Implements codeschool.models.cs.* namespace in which models from other
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
