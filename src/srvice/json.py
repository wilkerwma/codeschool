#
# Define json extensions for specific types
#
from functools import singledispatch
import numbers
import collections
import base64
import json as _json
import datetime
NoneType = type(None)


__all__ = ['loads', 'dumps', 'register', 'encode', 'decode']
__decode_registry__ = {}
__supported_encoders__ = {
    # Builtin types
    int, float, list, tuple, dict, str, bool, NoneType,

    # Abstract types
    numbers.Real, collections.Sequence, collections.Mapping
}


#
# Registration and basic APIs
#
def register(cls, name=None, encode=None, decode=None):
    """Register encode/decode functions for the given Python type.

    The name parameters refers to the value that is associated to the "@"
    key in the resulting dictionary. It is the encoder's responsability to add
    this key."""

    if name is None and decode:
        raise ValueError('cannot register decoder without knowing its name.')
    elif name in __decode_registry__:
        raise ValueError('an decoder already exists for "%s"' % name)
    elif decode:
        __decode_registry__[name] = decode

    if encode:
        if cls in __supported_encoders__:
            tname = cls.__name__
            raise ValueError('encoder already exists for %s objects' % tname)
        __supported_encoders__.add(cls)
        globals()['encode'].registry(cls)(encode)


def decode(data):
    """Decode a JSON-like structure into the corresponding Python data."""

    if isinstance(data, dict):
        if '@' in data:
            decoder = __decode_registry__[data['@']]
            return decoder({k: v for (k, v) in data.items() if k != '@'})
    return data


def _decode_register(cls, name=None):
    """Decorator that register decoding functions."""

    if name is None:
        name = cls.__name__.lower()

    def decorator(func):
        register(cls, name, decode=func)
        return func

    return decorator


decode.register = _decode_register


@singledispatch
def encode(data):
    """Encode some arbitrary Python data into a JSON-compatible structure.

    This naive implementation does not handle recursive structures. This might
    change in the future.

    This function encode subclasses of registered types as if they belong to
    the base class. This is convenient, but is potentially fragile and make
    the operation non-invertible.
    """

    if isinstance(data, (int, float, str, bool, NoneType)):
        return data

    type_name = type(data).__name__
    raise TypeError('could not encode %s object: %s' % (type(data), type_name))


def loads(data):
    """Load a string of JSON-encoded data and return the corresponding Python
    object."""

    return decode(_json.loads(data))


def dumps(obj):
    """Return a JSON string dump of a Python object."""

    return _json.dumps(encode(obj))


#
# Specialized encoding/decoding functions
#

# Fast-track atomic types
@encode.register(int)
@encode.register(float)
@encode.register(str)
@encode.register(bool)
@encode.register(NoneType)
def _(data):
    return data


# Generic numeric data
@encode.register(numbers.Real)
def _(data):
    return float(data)


# Dictionaries
@encode.register(collections.Mapping)
def _(data):
    encoded = {str(k): encode(v) for (k, v) in data.items()}
    if '@' in data:
        return {'@': 'object', 'data': encoded}
    return encoded


@decode.register(dict, 'object')
def _(data):
    return {k: decode(v) for (k, v) in data.items()}


# Lists and sequences
@encode.register(collections.Sequence)
def _(data):
    return [encode(x) for x in data]


# Binary data
@encode.register(bytes)
def _(data):
    data = base64.b64encode(data).decode('ascii')
    return {'@': 'bytes', 'data': data}


@decode.register(bytes)
def _(data):
    return data['data']


# Dates
@encode.register(datetime.date)
def _(date):
    return {
        '@': 'date',
        'year': date.year,
        'month': date.month,
        'day': date.day
    }


@decode.register(datetime.date, 'date')
def _(data):
    return datetime.date(data['year'], data['month'], data['day'])
