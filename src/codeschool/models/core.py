"""
Common classes and fields for all Codeschool apps.

This module imports lots of third party fields and models classes and should
be used as a drop-in replacement to django.db.models module.

The database should not be touched here. This module should only host abstract
models
"""
from django.db.models.fields.reverse_related import OneToOneRel as _OneToOneRel
from django.db.models import Model, Manager, QuerySet, DateField
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User, Group, AnonymousUser
from model_utils import Choices
from model_utils import managers as _mu_managers
from model_utils.managers import InheritanceManager, QueryManager
from model_utils.models import TimeStampedModel, TimeFramedModel, StatusModel
from codeschool.utils import lazy


# Adds the decorated method to the given class
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
class InheritableModel(Model):
    """A model with an InheritanceManager manager.

    When used with multiple inheritance, it generally should be the first base
    class.
    """

    class Meta:
        abstract = True

    objects = InheritanceManager()

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

    def as_subclass(self):
        for sub in reversed(self.get_subclasses()):
            try:
                return getattr(self, sub.__name__.lower())
            except AttributeError:
                pass
        return self


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


class DateFramedModel(Model):
    """Like a :cls:`TimeFramedModel`, but it's start and end fields are dates
    rather than datetimes."""

    class Meta:
        abstract = True

    start = DateField(_('start'), null=True, blank=True)
    end = DateField(_('start'), null=True, blank=True)
