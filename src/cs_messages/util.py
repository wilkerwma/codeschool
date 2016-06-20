"""
Uses an extended version of django.messages framework API to register
messages.
"""


def add_message(user, status, message, message_class=None, **kwargs):
    """
    Adds a new message associated with the user or request.

    This function accepts either a request or an user object. Messages tied to
    a request live only the duration of that given request and cannot be
    persistent. Messages tied to the user are stored into the database and can
    be persistent or not (the default behavior is to deactivate the message as
    soon as the user has read it).
    """
    # We import here to avoid problems with django initialization routines
    from codeschool.models import User
    if message_class is None:
        from cs_messages.models import Message as message_class

    return message_class.objects.create(
        message_to=user,
        status=status,
        payload=message,
        **kwargs
    )


def debug(user, message, **kwargs):
    """
    Adds a debug message.

    Accepts all arguments as :func:`add_message`, except the status, which is
    fixed to DEBUG.
    """

    from cs_messages.models import Message
    return add_message(user, Message.DEBUG, message, **kwargs)


def info(user, message, **kwargs):
    """
    Adds an info message.

    Accepts all arguments as :func:`add_message`, except the status, which is
    fixed to INFO.
    """

    from cs_messages.models import Message
    return add_message(user, Message.INFO, message, **kwargs)


def success(user, message, **kwargs):
    """
    Adds a success message.

    Accepts all arguments as :func:`add_message`, except the status, which is
    fixed to SUCCESS.
    """

    from cs_messages.models import Message
    return add_message(user, Message.SUCCESS, message, **kwargs)


def warning(user, message, **kwargs):
    """
    Adds a warning message.

    Accepts all arguments as :func:`add_message`, except the status, which is
    fixed to WARNING.
    """

    from cs_messages.models import Message
    return add_message(user, Message.WARNING, message, **kwargs)


def error(user, message, **kwargs):
    """
    Adds an error message.

    Accepts all arguments as :func:`add_message`, except the status, which is
    fixed to ERROR.
    """

    from cs_messages.models import Message
    return add_message(user, Message.ERROR, message, **kwargs)


#
# Message retrieval
#
def get_messages(user):
    """Return a sequence with all active messages related to the user."""

    if isinstance(user_or_request, models.User):
        user = user_or_request

        # Fetch messages
        return NotImplemented
    else:
        return user_or_request.messages


def count_messages(user):
    """Return the number of unread messages for the user or request."""

    return NotImplemented