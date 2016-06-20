from markdown import markdown
from django.db import models, transaction
from django.utils.translation import ugettext_lazy as _
from django.utils.text import slugify
from wagtail.wagtailcore.models import Page
from wagtail.wagtailcore.fields import RichTextField
from wagtail.wagtailadmin.edit_handlers import FieldPanel
from viewpack.types import DetailObject
from .mixins import MigrateMixin
from .serialize import SerializationMixin


class PageSerializationMixin(SerializationMixin):
    """
    A serializable page.
    """
    _serialization_exclude_fields = {
        'id', 'path', 'depth', 'numchild', 'slug', 'has_published_changes',
        'url_path', 'content_type_id', 'page_ptr_id', 'owner_id',
        'latest_revision_created_at', 'first_published_at',
    }


class CodeschoolPageMixin(PageSerializationMixin):
    """
    Extend wagtail's page with some extra functionality.
    """

    # cache parent link for creating objects in a consistent
    # tree state.
    __parent = None
    __db = None

    # a list of children scheduled to be saved when the page
    # gain a pk
    __children = ()

    #: Alias for page.title
    name = property(lambda x: x.title)

    #: Default content color
    content_color = "#10A2A4"

    @name.setter
    def name(self, value):
        self.title = value

    def __init__(self, *args, **kwargs):
        # Try to obtain the value for the parent page element.
        parent = kwargs.pop('parent_page', None)
        if parent is not None:
            if not isinstance(parent, Page):
                name = parent.__class__.__name__
                raise TypeError(
                    'The parent page must be a Page instance. got %s.' % name
                )
            self.__parent = parent
        super().__init__(*args, **kwargs)

    def __save_to_parent(self, *args, **kwargs):
        """
        Saves the model using the __parent reference to insert it in the correct
        point in the tree.
        """

        # If not parent is set, we use the default save method from super()
        if self.__parent is None:
            kwargs.setdefault('using', self.__db)
            return super().save(*args, **kwargs)

        # Parent must be saved into the database.
        if self.__parent.id is None:
            raise ValueError('parent must be saved into the database!')

        # Now we have to construct all path, depth, etc info from the parent.
        # It seems that there is a bug in add_child() method that prevent it
        # from calculating the correct path when the parent has not children
        parent, self.__parent = self.__parent, None
        self.depth = parent.depth + 1
        self.url_path = '%s/%s/' % (parent.url_path.rstrip('/'), self.slug)
        self.numchild = 0
        if parent.numchild == 0:
            self.path = parent.path + '0001'
        else:
            last_sibling = parent.get_last_child()

            if last_sibling is None:
                # The tree is possibly in an inconsistent state: the parent
                # claims to have a child, but has no last child.
                raise RuntimeError('invalid tree: %s',
                                   parent.get_parent().find_problems(),
                                   parent.numchild, parent.get_children())
            else:
                self.path = last_sibling._inc_path()

        # Save self and parent
        with transaction.atomic():
            super().save(*args, **kwargs)
            parent.numchild += 1
            parent.save(update_fields=['numchild'])

    def get_parent(self, *args):
        """
        Returns the parent node.
        """

        if self.__parent is None:
            return super().get_parent(*args)
        return self.__parent

    def set_parent(self, parent):
        """
        Sets the parent node link.
        """

        if self.id is None:
            self.__parent = parent
            self.path = None
            self.url_path = None
            self.depth = self.__parent.depth + 1
        else:
            self.move(parent)

    def get_default_parent(self):
        """
        Return the default parent instance if no parent is set.
        """
        from cs_core.models import rogue_root

        return rogue_root()

    def save(self, *args, **kwargs):
        # Prepare fields
        if self.id is None:
            self.prepare_create()
        else:
            self.prepare_save()

        # We check if __parent is set. This should only happen if pk is None.
        # If parent is set, we *do not* call the super save method. Instead,
        # we add_child() the parent node and remove the __parent reference.
        if self.__parent is not None:
            assert self.id is None
            self.__save_to_parent(*args, **kwargs)

        # Now we do not set an explicit parent, but it would be required to save
        # the model anyway. We ask for the default parent page and proceed
        elif self.pk is None and not self.path:
            self.__parent = self.get_default_parent()
            self.__save_to_parent(*args, **kwargs)
        else:
            kwargs.setdefault('using', self.__db)
            super().save(*args, **kwargs)

        # Save any children nodes, if they exist.
        if self.__children:
            with transaction.atomic():
                for add_child in self.__children:
                    self.add_child(**add_child)

        # Clean temporary fields
        if self.__db:
            del self.__db
        if self.__parent:
            del self.__parent
        if self.__children:
            del self.__children

    def prepare_create(self):
        """
        Called just before saving an element without a pk.

        This method fills up any required fields that were not set up during
        initialization.
        """
        self.slug = self.slug or slugify(self.title)

    def prepare_save(self):
        """
        Called just before saving an element with a pk.

        This method fills up any required fields that were not set up during
        initialization.
        """

        self.slug = self.slug or slugify(self.title)
        if self.depth is None and self.path:
            self.depth = len(self.path) // 4
        elif self.depth is None:
            self.depth = 0

    def add_child(self, **kwargs):
        """
        Add a new child element in the page.

        This method accepts the insertion of child nodes even before the page
        gains a pk attribute. This is done by defering the operation to a
        temporary list. Everything is then saved to the database when the
        save() method is called.
        """

        if self.pk is None:
            if 'instance' not in kwargs:
                raise ValueError('must specify an instance!')
            self.__children += kwargs,
        else:
            super().add_child(**kwargs)

    def get_template(self, request, *args, **kwargs):
        template = super().get_template(request, *args, **kwargs)
        if template.endswith('.html'):
            return template[:-5] + '.jinja2'
        return template

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)

        # Create an alias to "page" context variable to all page super classes
        for model in type(self).mro():
            if model not in BASE_CLASSES_BLACKLIST:
                if issubclass(model, Page):
                    context.setdefault(model.__name__.lower(), self)
        context.setdefault('object', self)

        # Sets the content color variable
        context.setdefault('content_color', self.content_color)

        # Sets model name and plural
        meta = self._meta
        context.setdefault('verbose_name', meta.verbose_name)
        context.setdefault('verbose_name_plural', meta.verbose_name_plural)

        #TODO: this is an ugly hack that should go away!
        obj = DetailObject(None)
        obj.object = self
        context.setdefault('detail_object', obj)
        description = getattr(self, 'long_description_html', None)
        if description:
            context['description'] = description
        return context

    def get_absolute_url(self):
        return self.url


class CodeschoolProxyPage(CodeschoolPageMixin, MigrateMixin, Page):
    """
    A base class for all codeschool page types that are proxies from wagtail's
    Page model.
    """

    class Meta:
        proxy = True
        app_label = 'cs_core'

    parent_page_types = []


class CodeschoolPage(CodeschoolPageMixin, MigrateMixin, Page):
    """
    Base class for all codeschool page types.

    This abstract class makes a few tweaks to Wagtail's default behavior.
    """

    class Meta:
        abstract = True

    page_ptr = models.OneToOneField(
        Page,
        parent_link=True,
        related_name='%(class)s_instance',
    )
    content_color = models.CharField(
        _('color'),
        max_length=20,
        default="#10A2A4",
        help_text=_('Personalize the main color for page content.'),
    )


class ShortDescribablePage(CodeschoolPage):
    """
    A describable page model that only adds the short_description field,
    leaving the long_description/body definition to the user.
    """
    class Meta:
        abstract = True

    short_description = models.CharField(
        _('short description'),
        max_length=140,
        blank=True,
        help_text=_('A very brief one-phrase description used in listings.'),
    )

    short_description_html = property(lambda x: markdown(x.short_description))

    def save(self, *args, **kwargs):
        self.seo_title = self.seo_title or self.short_description
        return super().save(*args, **kwargs)

    # Wagtail admin configurations
    content_panels = CodeschoolPage.content_panels + [
        FieldPanel('short_description'),
    ]


class DescribablePage(ShortDescribablePage):
    """
    A describable model that inherits from a wagtail's Page model and uses a
    RichTextField for its long_description field.
    """
    class Meta:
        abstract = True

    body = RichTextField(
        _('long description'),
        blank=True,
        help_text=_('A detailed explanation.')
    )

    # Html expansion of descriptions
    #long_description = property(lambda x: html_to_markdown(x.body))
    long_description = property(lambda x: x.body)


    @long_description.setter
    def long_description(self, value):
        self.body = markdown(value)

    long_description_html = property(lambda x: x.body)

    # Wagtail admin configurations
    content_panels = ShortDescribablePage.content_panels + [
        FieldPanel('body', classname="full"),
    ]


class RootList(CodeschoolPageMixin, Page):
    """
    Base class for all pages used as a root page in listings.
    """

    class Meta:
        proxy = True
        app_label = 'cs_core'

    short_description = ''
    short_description_html = ''
    long_description = ''
    long_description_html = ''

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(self, request, *args, **kwargs)
        context['object_list'] = (x.specific for x in self.get_children())
        return context


BASE_CLASSES_BLACKLIST = {
    RootList, DescribablePage, ShortDescribablePage, CodeschoolPage,
    CodeschoolPageMixin, PageSerializationMixin, CodeschoolProxyPage
}