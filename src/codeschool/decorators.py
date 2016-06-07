from django.contrib.auth.decorators import *


def teacher_login_required(func):
    """Decorator that marks a view as requiring a teacher login"""

    return login_required(func)


def student_login_required(func):
    """Decorator that marks a view as requiring a student login"""

    return login_required(func)


def login_required_method(func):
    """Decorates a method as @login_required, skipping the self argument"""

    @login_required
    def wrapped(request, self, *args, **kwds):
        return func(self, request, *args, **kwds)

    def decorated(self, request, *args, **kwds):
        return wrapped(request, self, *args, **kwds)

    return decorated