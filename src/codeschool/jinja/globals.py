from collections import UserDict


def template_vars(template):
    """Return the namespace defined in the template object."""

    try:
        return template._TemplateReference__context.vars
    except AttributeError:
        return UserDict(template)