from django.utils.html import escape
from djinga.register import jj_filter, jj_global


#@jj_filter
def markdown(text, *args, **kwargs):
    from markdown import markdown
    return markdown(text, *args, **kwargs)


def icon(value):
    if value is True:
        return '<i class="material-icons">done</i>'
    elif value is False:
        return '<i class="material-icons">error</i>'
    else:
        return '<i class="material-icons">%s</i>' % escape(value)
