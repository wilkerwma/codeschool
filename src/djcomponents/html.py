import collections
from django.utils.html import escapejs, escape
from djcomponents.core import Widget, AtomicWidget, attr_property, \
    tag_factory as _tag_factory


__all__ = [
    # Utilities
    'tag',

    # Text widgets
    'Text', 'HTMLText', 'Markdown', 'Script',

    # Forms
    'Input',

    # Lists
    'List', 'ListItem',

    # Misc
    'Div', 'Span', 'Anchor'
]


class TagManager:
    """
    Implements
    """

    TAG_REGISTRY = {}

    @classmethod
    def register(tagcls, tagname, **kwargs):
        """
        Register class to handle given tag.

        Optional kwargs can be passed to control the intialization of objects
        with the given tag.
        """

        def decorator(cls):
            tagcls.TAG_REGISTRY[tagname] = (cls, kwargs)
            return cls

        return decorator

    def __getattr__(self, tag):

        def method(*args, **kwargs):
            cls, defaults = self.TAG_REGISTRY.get(tag, (Widget, {}))
            kwargs = dict(defaults, **kwargs)
            return cls(*args, **kwargs)
        method.__name__ = tag
        method.__doc__ = 'Creates a new %s tag' % tag
        return method
tag = TagManager()


################################################################################
#                           Text-based widgets
################################################################################
@tag.register('text')
class Text(AtomicWidget):
    """
    A string of text.

    This differs from HTMLTextWidget since text is escaped during rendering.
    """

    def __init__(self, data, **kwargs):
        self.data = data
        super().__init__(**kwargs)

    def render(self):
        return escape(str(self.data))
Widget._text_widget = Text


@tag.register('html')
class HTMLText(Text):
    """
    An opaque string of HTML text.
    """

    def render(self):
        return str(self.data)


@tag.register('markdown')
class Markdown(Text):
    """
    A string of markdown text.

    This is converted to HTML during rendering.
    """

    def render(self):
        return markdown(str(self.data))


@tag.register('script')
class Script(Text):
    """
    A script tag with Javascript source.
    """
    def render(self):
        return '<script>%s</script>' % self.data


################################################################################
#                       HTML forms and input elements
################################################################################
@tag.register('input')
class Input(Widget):
    """
    Base class for widgets based on <input> html tags.
    """
    tag = 'input'

    def __init__(self, attrs=None, name=None, value=None, **kwargs):
        self.name = name
        self.value = value
        super().__init__(attrs, **kwargs)

    def _render_from_super(self, name=None, value=None, attrs=None, *args,
                           **kwargs):
        if name is None:
            name = self.name
        if value is None:
            value = self.value
        return super().render(name, value, attrs, *args, **kwargs)

    def render(self, *args, **kwargs):
        return self._render_from_super(*args, **kwargs)


################################################################################
#                              HTML lists
################################################################################
class ListMeta(type(Widget), type(collections.MutableSequence)):
    """
    Meta class for List types.
    """


@tag.register('ul')
@tag.register('ol', ordered=True)
class List(Widget, collections.MutableSequence, metaclass=ListMeta):
    """
    A list component.

    It chooses either <ul> or <ol> depending if the `ordered` parameter is False
    or True. Default is an unordered list.
    """
    tag = 'ul'
    ordered = property(lambda x: x.tag == 'ol')

    def __init__(self, data, *, ordered=False, **kwargs):
        if ordered and 'tag' not in kwargs:
            kwargs['tag'] = 'ol'
        super().__init__(**kwargs)

        for x in data:
            self.add_child(x)

    def __delitem__(self, idx):
        child = self.children.pop(idx)
        child.parent = None

    def __getitem__(self, idx):
        return self.children[idx]

    def __setitem__(self, idx, child):
        self.add_child(child)
        self.children[idx] = self.children.pop()

    def normalize_child(self, child):
        child = super().normalize_child(child)

        if not isinstance(child, ListItem):
            return ListItem(child)
        return child

    def insert(self, idx, child):
        self.add_child(value)
        self.children.insert(idx, self.children.pop())


@tag.register('li')
class ListItem(Widget):
    """
    A <li> item component. Used inside list elements.
    """
    tag = 'li'

    def __init__(self, data, **kwargs):
        super().__init__(**kwargs)
        self.add_child(data)



################################################################################
#                              HTML tables
################################################################################
class Table(Widget):
    """
    An HTML table.
    """


################################################################################
#                             Misc HTML tags
################################################################################
def tag_factory(tagname, *args, **kwargs):
    # Local override of tag_factory that register tag in the tag element.
    tag_cls = _tag_factory(tagname, *args, **kwargs)
    tag.register(tagname)(tag_cls)
    return tag_cls


Div = tag_factory('div')
Span = tag_factory('Span')


@tag.register('a')
class Anchor(Widget):
    """
    An html <a> element.
    """
    tag = 'a'
    default_attributes = {'alt': None, 'href': None}

    def __init__(self, *args, link_name=None, **kwargs):
        super().__init__(*args, **kwargs)
        if link_name:
            self.add_child(link_name)

    alt = attr_property('alt')
    href = attr_property('href')

    @property
    def link_name(self):
        return self.content_data

    @link_name.setter
    def link_name(self, value):
        self.clear_children()
        self.add_child(value)

