from viewpack.utils import lazy


CHECK_MRO = True
MRO_NEUTRAL = {
    'ParentTemplateNamesMixin.get_template_names',
    'ParentContextMixin.get_context_data',
    'SingleObjectMixin.get_context_data',
    'CanEditMixin.get', 'CanViewMixin.get', 'CanEditMixin.post',
}
MRO_STOP = {
    'TemplateResponseEndpointMixin.get_template_names':
        '*TemplateResponseMixin.get_template_names',
    'DetailView.get': '*BaseDetailView.get',
}


def mmro(cls, method):
    """
    Return a list of strings with the MRO for the given method in the class.
    """

    result = []
    for subclass in cls.mro():
        if method in subclass.__dict__:
            mark = '' if 'viewpack' in subclass.__module__ else '*'
            result.append('%s%s.%s' % (mark, subclass.__name__, method))
    return result


def check_mro(cls=None, *, ommit=()):
    """Checks if class define the correct MRO for all public method."""

    if cls is None:
        def decorator(cls):
            return check_mro(cls, ommit=ommit)

        return decorator

    if not CHECK_MRO:
        return cls

    # We assume that each class represents a re-implementation of its last base,
    # which should have the same class name
    original = cls.__bases__[-1]
    if cls.__name__ != original.__name__:
        raise ValueError('Should inherit from %s, got %s' %
                         (cls.__name__, original.__name__))

    # Now we check the mro of each public method. We expect that the derived
    # mro begins the same as the original one.
    for method in dir(cls):
        if method.startswith('_') or method in ommit:
            continue

        # Skip properties and constants
        value = getattr(cls, method)
        if isinstance(value, (property, lazy)):
            continue

        mro = mmro(cls, method)
        mro_original = mmro(original, method)
        mro_ = list(mro)
        mro_original_ = list(mro_original)

        # Remove neutral methods from both mro's. We break the mro in any
        # registered MRO_STOP method
        for L in [mro_, mro_original_]:
            for i, method in enumerate(L):
                if method in MRO_STOP:
                    L[i] = MRO_STOP[method]
                    L[:] = L[:i + 1]
                    break
            L[:] = [x.replace('*', '') for x in L if x not in MRO_NEUTRAL]

        # Check if both mro's begin the same
        if not all(x == y for (x, y) in zip(mro_, mro_original_)):
            raise AssertionError(
                'Got an unexpected mro for %s:\n' % cls.__name__ +
                '    %s\n    %s\nas\n    %s\n    %s\n' % (
                    mro, mro_original, mro_, mro_original_
                )
            )

    return cls