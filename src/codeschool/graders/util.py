import io
import sys
import signal
from threading import Thread
from django.utils.html import escape
from codeschool.graders import errors
_print_func = print


def example_to_html(example):
    '''Render a parsed IO template into HTML'''

    out = []
    if isinstance(example, str):
        return escape(example)
    for x in example:
        data = x.replace('\n', '<br>')  # TODO: proper HTML escaping
        if x.is_input:
            data = '<span style="color: #f00;">&lt;%s&gt;</span>' % data
            data += '<br>'
        out.append(data)
    return ''.join(out)  # + '<pre>%s</pre>' % (example)


def message_bad_format(got, expected):
    got = '<strong>Valor obtido</strong><br>' + example_to_html(got)
    expected = '<strong>Resposta esperada</strong><br>' + \
        example_to_html(expected)
    return '<div>%s<br><br>%s</div>' % (got, expected)


def message_from_exception(ex):
    return str(type(ex).__name__ + ': ' + str(ex))


def print_str(*args, **kwds):
    '''A print function that return the formatted string instead of printing
    it on screen'''

    out, err = sys.stdout, sys.stderr
    out_io = sys.stdout = sys.stderr = io.StringIO()
    try:
        _print_func(*args, **kwds)
    finally:
        sys.stdout, sys.stderr = out, err
    return out_io.getvalue()


def _timeout_handler(signum, frame):
    raise TimeoutError()


def timeout(func, args=(), kwargs={}, timeout=1.0, threading=True):
    '''Execute function with timeout.

    If timeout exceeds, raises a TimeoutError'''

    if threading:
        result = []
        exceptions = []

        def target():
            try:
                result.append(func(*args, **kwargs))
            except Exception as ex:
                exceptions.append(ex)

        thread = Thread(target=target)
        thread.start()
        thread.join(timeout)
        if thread.is_alive():
            raise TimeoutError
        else:
            try:
                return result.pop()
            except IndexError:
                raise exceptions.pop()
    else:
        signal.signal(signal.SIGALRM, _timeout_handler)
        signal.alarm(timeout)
        try:
            result = func(*args, **kwargs)
        finally:
            signal.alarm(0)

        return result
