from djcomponents import Widget
from django.db.models import QuerySet, Manager


class WidgetQuerySet:
    def __init__(self, qs):
        self._qs = qs

    def __getattr__(self, attr):
        value = getattr(self, attr)
        if isinstance(value, (QuerySet, Manager)):
            return WidgetQuerySet(value)
        else:
            return value


class SingleObjectWidgetMeta(type(Widget)):
    def __new__(cls, name, bases, ns):
        new = super().__new__(cls, name, bases, ns)
        new.objects = WidgetQuerySet(new.model.objects)
        return new


class SingleObjectWidget(Widget, metaclass=SingleObjectWidgetMeta):
    """
    A widget associated with some object type.
    """

    model = None


class DetailWidget(Widget):
    """
    A widget that offers a "detail" view for some object.
    """


class FormWidget(Widget):
    """
    A widget that displays a form.
    """


class CreateWidget(FormWidget):
    """
    A widget that displays a model form for creating a new object from a model.
    """


class EditWidget(CreateWidget, SingleObjectWidget):
    """
    A widget that displays a model form for editing some object.
    """
