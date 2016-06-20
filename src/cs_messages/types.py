"""
Auxiliary types for the codeschool messaging app
"""
from collections import Sequence
from django.db.models import Model


class MessageList(Sequence):
    """
    A list-like structure that stores messages and mark them as read as soon as
    they are consumed.
    """

    def __init__(self, user, filters=None):
        from cs_messages.models import Message

        self._messages = Message.objects.filter(is_active=True)
        if isinstance(filters, int):
            self._messages = self._messages.filter(status=True)
        elif isinstance(filters, Sequence):
            self._messages = self._messages.filter(status__in=filters)

    def __getitem__(self, index):
        return self._messages[index]

    def __iter__(self):
        for message in self._messages:
            message.mark_read()
            yield message

    def __len__(self):
        return self._messages.count()

    def filter(self, filters=None):
        """
        Return an iterable sequence of messages that can be filtered to some
        specific status values.
        """

        return MessageList(self._messages, filters)


class ModelProxy:
    """
    A pickable proxy for a Django model.
    """

    def __init__(self, model_or_pk, model_class=None):
        if isinstance(model_or_pk, Model):
            self.__dict__['pk'] = model_or_pk.pk
            self.__model = model_or_pk
            model_class = type(model_or_pk)
        else:
            self.pk = model_or_pk
            self.__model = model_class.objects.get(pk=self.pk)
        self.__class = model_class

    def __getstate__(self):
        data = dict(self.__dict__)
        del data['pk']
        del data['_ModelProxy__class']
        del data['_ModelProxy__model']
        return self.pk, self.__class, data

    def __setstate__(self, state):
        self.pk, model_class, data = state
        self.__model = model_class.objects.get(pk=self.pk)
        for k, v in data.items():
            setattr(self, k, v)

    def __getattr__(self, attr):
        return getattr(self.__model, attr)

    def __setattr__(self, attr, value):
        if not attr.startswith('_') and hasattr(self.__model, attr):
            setattr(self.__model, attr, value)
        else:
            self.__dict__[attr] = value

    def __repr__(self):
        return repr(self.__model)

    def __str__(self):
        return str(self.__model)
