The easiest way to use ``srvice`` is to include it as dependency in your
project's ``requirements.txt`` or in the ``install_requires`` field in
``setup.py``. You can install srvice is using pip::

    $ python -m pip install srvice

and start using it immediately.

Even though ``srvice`` requires Django to work, it does not define any model or
template and hence it is not necessary to include it in the INSTALLED_APPS list
in ``settings.py``