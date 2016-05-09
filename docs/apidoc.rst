=============
API Reference
=============

Markio is very simple to use. Users may want to use the :func:`parse`  and
:func:`parse_string``functions::

    >>> import markio
    >>> parsed = makrio.parse('hello-person.markio')
    >>> parsed.title
    'Hello Person'

The ``parsed`` structure is a simple dictionary that maps each section of the
markdown file to its corresponding content.

.. automodule:: markio
   :members: