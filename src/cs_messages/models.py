import json
from collections import Sequence
from django.db import models
from django.utils.html import escape
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey
from codeschool import models
from cs_messages.types import MessageList, ModelProxy


class Message(models.TimeStampedModel, models.PolymorphicModel):
    """
    Represents notifications from Django subsystems to users.
    """

    DEBUG = 10
    INFO = 20
    SUCCESS = 25
    WARNING = 30
    ERROR = 40
    STATUS_CHOICES = (
        (DEBUG, 'debug'),
        (INFO, 'info'),
        (SUCCESS, 'success'),
        (WARNING, 'warning'),
        (ERROR, 'error'),
    )
    STATUS_MAP = dict(STATUS_CHOICES)

    message_to = models.ForeignKey(
        models.User,
        null=True,
        help_text=_('User instance recipient of the message'),
    )
    # Arbitrary object that sent the message. We use the GenericKey mechanism
    # in order to store a relation to an arbitrary object
    message_from_id = models.IntegerField(blank=True, null=True)
    message_from_type = models.ForeignKey(
        models.ContentType,
        null=True,
        blank=True,
    )
    message_from = GenericForeignKey(
        'message_from_type',
        'message_from_id'
    )
    status = models.IntegerField(
        choices=STATUS_CHOICES,
        default=INFO,
    )
    is_read = models.BooleanField(
        default=False,
        help_text=_('Was message read by the recipient?')
    )
    is_active = models.BooleanField(
        default=True,
        help_text=_('Is message active')
    )
    is_persistent = models.BooleanField(
        default=False,
        help_text=_(
            'True if the the user needs to explicitly de-activate the message '
            'to make it inactive.'
        )
    )
    payload = models.PickledObjectField(
        help_text=_('Arbitrary object payload sent with the message'),
        null=True,
        blank=True
    )

    def __html__(self):
        # Jinja tries this method before __str__ to render html content.
        return self.render()

    def __repr__(self):
        username = self.message_to.username
        data = repr(self.payload)
        if len(data) >= 15:
            data = data[:min(12, len(data) - 3)] + '...'
        return "<Message: to=%s, data=%s>" % (username, data)

    def __str__(self):
        return self.render()

    def render(self):
        """
        Renders message in HTML.

        The default strategy is to call the .render() method of the payload
        object, if it exists. If payload is a string of text, it is rendered
        with HTML-escape enabled.

        This model derives from django-polymorfic. If you need an specialized
        rendering strategy, you can create proxy subclasses that override this
        method::

            class PersonalizedMessage(Message):
                class Meta:
                    proxy = True

                def render(self):
                    return '<p>Hello, %s!</p>' % self.payload
        """
        try:
            return self.payload.render()
        except AttributeError:
            return escape(self.payload)

    def mark_read(self):
        """
        Mark message as read. This may deactivate the message if it is not
        persistent.
        """

        self.is_read = True
        if not self.is_persistent:
            self.is_active = False
        self.save()

    def deactivate(self, mark_read=False):
        """
        Explicitly deactivates message.

        If mark_read is True it also marks the message as read.
        """

        if mark_read:
            self.is_read = True
        self.is_active = False
        self.save()

    def payload_to_json(self):
        """
        Return a JSON-compatible representation of the payload to be sent to
        the client.

        The default implementation returns the payload if it is a JSON
        compatible type. Sub-classes may adopt different strategies.
        """

        # Fasttrack atomic JSON elements
        if isinstance(self.payload, (int, float, str, bool, type(None))):
            return self.payload

        # Convert to assert that data is JSON-compatible.
        return json.loads(json.dumps(self.payload))

    def sender_to_json(self):
        """
        Return a JSON-compatible representation of the sender to be sent to
        the client.

        The default implementation sends the primary key if the sender is
        defined.
        """
        if self.message_from is not None:
            return self.message_from_id, self.message_from_type_id
        return None

    def to_json(self):
        """
        Return a JSON-compatible representation of the message to be sent to
        the client.
        """
        return {
            'message_to': self.message_to.username,
            'message_from': self.sender_to_json(),
            'status': self.STATUS_MAP[self.status],
            'payload': self.payload_to_json(),
            'is_active': self.is_active,
            'is_read': self.is_read,
            'is_persistent': self.is_persistent,
        }

