import functools
import contextlib

USE_DB = True


def use_db():
    """Return True if it should try to use the database or False otherwise.

    This function is used to aid tests. It signals to functions that may return
    mocks or unsaved models that it is running on a unittest suite that does
    not expect db access."""

    return USE_DB


def ask_use_db(value):
    """Return the result of uses_db() if value is None or value otherwise.

    This function is useful for setting the correct behavior from a default
    None uses_db attribute.
    """

    if value is None:
        return USE_DB
    else:
        return value


def nodb(func=None):
    """
    Makes the use_db() function return False inside a block of code. This
    tells functions that support this feature to do not touch the database.

    Can be used either as a context manager or as a function decorator
    """

    if func is None:
        return _nodb_context_manager()
    else:
        @functools.wraps(func)
        def decorated(*args, **kwargs):
            with _nodb_context_manager():
                result = func(*args, **kwargs)
            return result
        return decorated


@contextlib.contextmanager
def _nodb_context_manager():
    # Context manager implementation
    global USE_DB

    try:
        USE_DB = False
        yield
    finally:
        USE_DB = True


def saving(obj, *args, **kwags):
    """Calls obj.save(**kwargs) and then return object.

    If an extra positional argument is given, it should be either None or a
    boolean. If False, it skips saving. If None, it uses the value of use_db()
    in order to decide it the object should be saved or not."""

    # Should we save?
    save = True
    if args:
        save, = args
        save = use_db() if save is None else save

    # Save and return
    if save:
        obj.save(**kwags)
    return obj
