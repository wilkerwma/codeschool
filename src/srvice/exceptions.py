__all__ = ['Error', 'EvalError', 'InternalError', 'RangeError',
           'ReferenceError', 'URIError']

# Javascript exception aliases
Error = Exception


class EvalError(Exception):
    """
    Error regarding the use of js function eval()
    """


class InternalError(RuntimeError):
    """
    Internal error on the js engine.
    """


class RangeError(IndexError, OverflowError):
    """
    Error on numerical ranges of values.
    """


class ReferenceError(Exception):
    """
    Error occurs when de-referencing an invalid reference.
    """


class URIError(ValueError):
    """
    Error when deconding/encoding invalid URIs.
    """
