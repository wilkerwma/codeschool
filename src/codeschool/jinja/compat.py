from functools import singledispatch
import types


@singledispatch
def django_compat_finalizer(x):
    return str(x)


@django_compat_finalizer.register(types.MethodType)
@django_compat_finalizer.register(types.BuiltinMethodType)
@django_compat_finalizer.register(types.FunctionType)
@django_compat_finalizer.register(types.BuiltinFunctionType)
def _(func):
    return django_compat_finalizer(func())
