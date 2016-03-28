from django.contrib.auth.decorators import *


def teacher_login_required(func):
    """Decorator that marks a view as requiring a teacher login"""

    return login_required(func)


def student_login_required(func):
    """Decorator that marks a view as requiring a student login"""

    return login_required(func)
