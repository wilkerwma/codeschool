from viewpack.utils import delegate_to_parent
from viewpack import permissions


class CanViewMixin:
    """
    Adds the can_view() method which is called before get() and post() to check
    if the request is valid or not.
    """
    check_permissions = delegate_to_parent('check_permissions', False)
    raise_404_on_permission_error = delegate_to_parent('check_permissions', True)

    def get(self, request, *args, **kwargs):
        return (_check_permission_then_go(self, 'view') or
                super().get(request, args, kwargs))

    def can_view(self):
        """
        Return True if the current user can view object and False otherwise.

        This method tries to execute the parent's can_view method. If it does
        not exist, it uses :func:`viewpack.permissions.can_view`.
        """
        if not self.check_permissions:
            return True
        elif hasattr(self.parent, 'can_view'):
            return self.parent.can_view(self.object)
        else:
            return permissions.can_view(self.object, self.request.user)


class CanEditMixin:
    """
    Adds the can_edit() method which is called before get() and post() to check
    if the request is valid or not.
    """
    check_permissions = delegate_to_parent('check_permissions', False)
    raise_404_on_permission_error = delegate_to_parent('check_permissions', True)

    def get(self, request, *args, **kwargs):
        return (_check_permission_then_go(self, 'edit') or
                super().get(request, args, kwargs))

    def post(self, request, *args, **kwargs):
        return (_check_permission_then_go(self, 'edit') or
                super().post(request, args, kwargs))

    def can_edit(self):
        """
        Return True if the current user can edit `self.object` and False
        otherwise.

        This method tries to execute the parent's can_edit method. If it does
        not exist, it uses :func:`viewpack.permissions.can_edit`.
        """
        if not self.check_permissions:
            return True
        elif hasattr(self.parent, 'can_edit'):
            return self.parent.can_edit(self.object)
        else:
            return permissions.can_edit(self.object, self.request.user)


class CanCreateMixin:
    """
    Adds the can_create() method which is called before get() and post() to check
    if the request is valid or not.
    """
    check_permissions = delegate_to_parent('check_permissions', False)
    raise_404_on_permission_error = delegate_to_parent('check_permissions', True)

    def get(self, request, *args, **kwargs):
        return (_check_permission_then_go(self, 'create') or
                super().get(request, args, kwargs))

    def post(self, request, *args, **kwargs):
        return (_check_permission_then_go(self, 'create') or
                super().post(request, args, kwargs))

    def can_create(self):
        """
        Return True if the current user can create `self.object` and False
        otherwise.

        This method tries to execute the parent's can_edit method. If it does
        not exist, it uses :func:`viewpack.permissions.can_edit`.
        """
        if not self.check_permissions:
            return True
        elif hasattr(self.parent, 'can_create'):
            return self.parent.can_create(self.object)
        else:
            return permissions.can_create(self.object, self.request.user)


def _check_permission_then_go(self, permission):
    """Auxiliary function that implements permission check before proceeding.

    Args:
        self:
            View instance
        permission:
            String with permission name (e.g.: 'edit', 'view', etc)
    """

    self.object = self.get_object()
    has_permission = getattr(self, 'can_' + permission)()
    if has_permission:
        return None
    elif self.raise_404_on_permission_error:
        raise http.Http404
    else:
        return http.HttpResponseForbidden(
            "You don't have permission to %s the requested object" % permission
        )