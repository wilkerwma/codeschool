import re
from functools import partial
from django.forms import widgets
from django.forms.utils import flatatt
from django.utils.html import escape, escapejs
DEBUG = True
__all__ = ['Widget', 'AtomicWidget', 'TemplateRenderMixin']


def attr_property(attr):
    """
    An attribute that mirrors data in an entry in the self.attrs dictionary.
    """

    def fget(self):
        return self.attrs.get(attr)

    def fset(self, value):
        self.attrs[attr] = value
        if value == self.default_attributes.get(attr):
            del self.attrs[attr]

    return property(fget, fset)


class WidgetMeta(type):
    """
    Metaclass for Widget types.

    This class register media resources associated to widget during widget's
    creation
    """


class Widget(metaclass=WidgetMeta):
    """
    Base class for all widget components.
    """

    tag = None
    tag_closes = True
    required_classes = ()

    # Global HTML attributes with a python interface
    #: HTML id for widget
    id = attr_property('id')

    #: Lang value for i18n
    lang = attr_property('lang')

    #: If true, element exists in the DOM, but is not visible.
    hidden = attr_property('hidden')

    #: The CSS style attribute that is applied to element.
    style = attr_property('style')

    #: Title for element.
    title = attr_property('title')

    #: Global attributes without a python interface:
    default_attributes = dict(
        accesskey=None,
        contenteditable=None,
        contextmenu=None,
        dir=None,
        draggable=False,
        dropzone=None,
        itemid=None,
        itemref=None,
        itemscope=None,
        itemtype=None,
        spellcheck=None,
        tabindex=None,
        translate=None,
    )

    def __init__(self, *,
                 parent=None,
                 id=None, classes=None,
                 tag=None, tag_closes=None, **kwargs):

        # Save basic attributes
        self.parent = None
        self.children = []
        self.attrs = {}

        # Tag info
        if tag is not None:
            self.tag = tag
        if tag_closes is not None:
            self.tag_closes = tag_closes

        # Save html attributes
        if id:
            self.attrs['id'] = id
        if classes:
            if isinstance(classes, str):
                classes = classes.split()
            self.classes = list(classes or ())

        # Register to parent, if necessary
        if parent:
            parent.add_child(self)

        # Save extra attributes, if not the default values
        for attr, v in kwargs.items():
            try:
                default = self.default_attributes[attr]
                if v != default:
                    setattr(self, attr, v)
            except KeyError:
                raise TypeError('invalid argument: %s' % attr)

    def render_attrs(self, attrs=None):
        """
        Return a formatted string of attributes that can be inserted in the
        opening tag for the HTML widget.
        """

        return flatatt(dict(self.attrs, **(attrs or {})))

    def render_tag_open(self, tag=None, attrs=None):
        """
        Renders the opening tag for widget, including attributes.
        """

        if tag is None:
            tag = getattr(self, 'tag', 'div')
        return '<%s%s>' % (tag, self.render_attrs(attrs))

    def render_tag_close(self, tag=None):
        """
        Renders the closing tag for widget.
        """

        if tag is None:
            tag = getattr(self, 'tag', 'div')
        return '</%s>' % tag

    def render_content_data(self):
        """
        Render the HTML content of all children.
        """
        return ''.join(x.render() for x in self.children)

    def render(self, pretty=None):
        """
        Renders widget as an HTML source.
        """

        if self.children:
            html = '%s%s%s' % (self.tag_open, self.content_data, self.tag_close)
        elif self.tag_closes:
            html = '%s%s' % (self.tag_open, self.tag_close)
        else:
            html = self.tag_open

        if pretty is None:
            pretty = DEBUG
        return prettify_html(html) if pretty else html

    attrs_string = property(lambda x: x.render_attrs())
    tag_open = property(lambda x: x.render_tag_open())
    tag_close = property(lambda x: x.render_tag_close())
    content_data = property(lambda x: x.render_content_data())

    @property
    def classes(self):
        return (self.attrs.get('class') or '').split()

    @classes.setter
    def classes(self, value):
        if isinstance(value, str):
            value = value.split()

        required = self.required_classes
        value = required + tuple(x for x in value if x not in required)
        self.attrs['class'] = ' '.join(escape(x) for x in value)

    def normalize_child(self, child):
        """
        Transform child into a Widget instance before adding it to the list
        of children.

        This function may be implemented in subclasses in order to validate
        child elements before insertion.
        """

        if isinstance(child, Widget):
            return child
        elif isinstance(child, (str, int, float, complex, bool)):
            return self._text_widget(child)
        else:
            raise TypeError('invalid child type: %s' % type(child).__name__)

    def add_child(self, child):
        """
        Adds a child widget to the list of children.
        """

        child = self.normalize_child(child)
        if child.parent is None or child.parent is self:
            child.parent = self
            self.children.append(child)
        else:
            raise ValueError('children already has parent')

    def remove_child(self, child):
        """
        Remove child node.
        """

        for idx, elem in self.children:
            if elem is child:
                del self.children[idx]
                child.parent = None
                break
        else:
            raise ValueError('%r is not a children' % child)

    def clear_children(self):
        """Remove all children elements."""

        for child in self.children:
            child.parent = None
        self.children[:] = []

    def __contains__(self, child):
        return child in self.children

    def __iter__(self):
        return iter(self.children)

    def __len__(self):
        return len(self.children)

    def __html__(self):
        return self.render()

    def __str__(self):
        return self.render()


class AtomicWidget(Widget):
    """
    A widget class that has no children.
    """

    def add_child(self, child):
        name = type(self).__name__
        raise TypeError('%s widgets have no children' % name)


class TemplateRenderMixin:
    """
    Mixin that dsf
    """
    template_name = None

    def render(self, template_name=None, **kwargs):
        """
        Use template defined by "template_name" or "self.template_name" to
        render the widget.
        """

        context = self.render_context()
        template_name = template_name or self.template_name
        return render_to_string(template_name, context,
                                request=self.request, **kwargs)

    def render_context(self):
        raise NotImplementedError(
            'Subclasses must implement the render_context() function that'
            'return a context dictionary that should be passed to the '
            'template.')


def tag_name(tag):
    """
    Return the tag name from a tag specification.

    Example::

    >>> tag_name('<a href="foo">')
    'a'
    >>> tag_name('</a>')
    'a'
    """

    start = 1
    if tag.startswith('</'):
        start += 1
    idx = start

    while tag[idx].isalpha() or tag[idx] == '-':
        idx += 1
    return tag[start:idx]


def prettify_html(html, spaces=4):
    """
    Return a pretty-printed version of the html fragment string.
    """
    # It only works with compact tags. We split at the >< point in which the
    # closing tag and the opening tag encounter.
    data = html.split('><')
    if len(data) == 1:
        return html

    elements = ['<%s>' % x for x in data]
    elements[0] = elements[0][1:]
    elements[-1] = elements[-1][:-1]
    indent = ' ' * spaces

    nesting = []
    for idx, elem in enumerate(elements):
        tag = tag_name(elem)
        close_tag = '</%s>' % tag

        if elem == close_tag:
            while nesting[-1] != tag:
                nesting.pop()
            nesting.pop()

        elements[idx] = indent * len(nesting) + elem

        if not elem.endswith(close_tag):
            nesting.append(tag)

    return '\n'.join(elements)


def tag_factory(tagname,
                classname=None,
                tag_closes=True,
                classes=None,
                attrs=None):
    """
    Creates a new Widget factory for the given HTML tag.

    Args:
        tagname:
            HTML tag name.
        classname:
            The name of the python widget class.
        tag_closes:
            If True (default), tag requires a closing tag.
        attrs:
            Dictionary mapping python-visible attributes to their default
            values.
        classes:
            If given, define a list of css classes that are always applied to
            instances.
    """

    ns = {'tag': tagname, 'tag_closes': tag_closes}
    if classes:
        ns['required_classes'] = dict(classes)
    if attrs:
        ns['default_attributes'] = dict(attrs)
        for attr, value in attrs.items():
            ns[attr] = attr_property(attr)

    return type(classname or tagname.title(), (Widget,), ns)
