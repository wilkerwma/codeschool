from functools import singledispatch


@singledispatch
def can_download(obj, user, format=None):
    """
    Return True if user can download the given object in the requested format.

    This function accepts single argument dispatch.
    """

    if hasattr(obj, 'can_download'):
        return obj.can_download(user, format=format)
    return can_edit(obj, user)


@singledispatch
def can_edit(obj, user):
    """
    Return True if user can edit the given object.

    This function accepts single argument dispatch.
    """

    if hasattr(obj, 'can_edit'):
        return obj.can_edit(user)
    else:
        #TODO: check permissions
        return False


@singledispatch
def can_view(obj, user):
    """
    Return True if user can view the given object.

    This function accepts single argument dispatch.
    """

    if hasattr(obj, 'can_view'):
        return obj.can_view(user)
    else:
        #TODO: check permissions
        return False


@singledispatch
def can_create(cls, user):
    """
    Return True if user can create new objects of the given type.

    This function accepts single argument dispatch.
    """

    if hasattr(cls, 'can_create'):
        return cls.can_create(user)
    else:
        #TODO: check permissions
        return False

