from docutils import core
from docutils.core import publish_parts
from docutils.writers.html4css1 import Writer, HTMLTranslator
from django.template import Library
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe
register = Library()


class NoHeaderHTMLTranslator(HTMLTranslator):

    def __init__(self, document):
        HTMLTranslator.__init__(self, document)
        self.head_prefix = ['', '', '', '', '']
        self.body_prefix = []
        self.body_suffix = []
        self.stylesheet = []

_w = Writer()
_w.translator_class = NoHeaderHTMLTranslator


def reSTify(string):
    return core.publish_parts(string, writer=_w)['html_body']


@register.filter
@stringfilter
def reST(data):
    '''Convert restructuredText to html'''

    data = data.replace('\r\n', '\n')
    #data = publish_parts(data, writer_name='html')['html_body']
    data = reSTify(data)
    return mark_safe(data)


if __name__ == '__main__':
    print(reST('foo::\n\n\tx\n\ty'))