from functools import partial
import types
from srvice.decorators import api


class ACMetaInfo:
    roles = ['nobody', 'viewer', 'creator', 'editor', 'owner']
    nobody_fields = []
    viewer_fields = []
    editor_fields = []
    owner_forbidden = []

    def __init__(self, meta_cls):
        self.data = vars(meta_cls())


class ModelACMeta(type):
    pass


class ModelAC(metaclass=ModelACMeta):
    def __init__(self, obj, user):
        self._data = obj
        self._user = user
        self._role = self.get_role(user)
        self._forbidden = self._meta.forbidden(self._role)
        for attr in self._meta.fields(self._role):
            value = getattr(obj, attr)
            setattr(self, attr, value)

    def get_role(self, user):
        """
        Return the maximum set of permissions the user have on object.
        """

        if self.rbac_owner(user):
            return 'owner'
        elif self.rbac_editor(user):
            return 'editor'
        elif self.rbac_creator(user):
            return 'creator'
        elif self.rbac_viewer(user):
            return 'viewer'
        else:
            return 'nobody'

    def rbac_owner(self, user):
        """
        Return True if user has 'owner' permissions.
        """

        return user.is_superuser or owns(user, self._data)

    def rbac_creator(self, user):
        """
        Return True if user has 'can_create' permissions.
        """

        return can_create(user, self._data)

    def rbac_viewer(self, user):
        """
        Return True if user has 'owner' permissions.
        """

        return can_edit(user, self._data)

    def rbac_editor(self, user):
        return can_edit(user, self._data)

    def __str__(self):
        return str(self._data)

    def __getattr__(self, attr):
        if attr in self._forbidden:
            raise PermissionError('No permission to access attribute %s' % attr)
        value = getattr(self._data, attr)
        if isinstance(value, types.MethodType):
            func = value.__func__
            return types.MethodType(func, self)
        raise AttributeError()


class MyModelAC(ModelAC):
    class Meta:
        model = foo
        view_fields = [1,2,3]
        edit_fields = [1,2,3,3]


def get_model(model):
    pass


@api
def get_object(request, model, **kwargs):
    model = get_model(model)
    obj = model.get(**kwargs)
    return rbac(obj, request.user)