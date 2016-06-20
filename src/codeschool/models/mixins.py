from django.db import models, transaction
from django.db.models import options
from django.apps import apps
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import FieldDoesNotExist
from django.core import serializers
from codeschool.utils import lazy

__all__ = [
    # Copy actions
    'CopyMixin', 'CopyableModel',

    # Named models
    'NamedModel', 'DescribableModel',

    # Other
    'MigrateMixin',
]


def html_to_markdown(value):
    """
    Converts html to markdown using html2text utility.
    """

    import html2text
    return html2text.html2text(value)


class CopyMixin:
    """
    Mixin class that implements a safe .copy() method to create copies of
    model instances even if they are model subclasses.
    """

    def copy(self, overrides=None, commit=True):
        """Return a copy of the object. If commit=False, the copy is not saved
        to the database.

        The optional overrides dictionary defines which attributes should be
        overridden in the copied object.
        """

        # Retrieve data
        data = {
            f.name: getattr(self, f.name)
            for f in self._meta.fields
            if not f.primary_key
        }

        # Save overrides
        if overrides:
            data.update(overrides)

        # Crete object
        new = type(self)(**data)
        if commit:
            new.save()
        return new


class CopyableModel(CopyMixin, models.Model):
    """
    Model that implements a copy() method from CopyMixin.
    """

    class Meta:
        abstract = True


class NamedModel(models.Model):
    """
    Model class that defines a uniform "name" CharField across all apps and
    models in codeschool.
    """

    class Meta:
        abstract = True

    name = models.CharField(
        _('name'),
        max_length=100
    )
    title = property(lambda x: x.name)

    def __str__(self):
        return self.name


class DescribableModel(NamedModel):
    """
    Mixin class that define uniform "name", "short_description" and
    "long_description" fields.
    """

    class Meta:
        abstract = True

    short_description = models.CharField(
        _('short description'),
        max_length=140,
        blank=True,
        help_text=_('A very brief one-phrase description used in listings.'),
    )
    long_description = models.TextField(
        _('long description'),
        blank=True,
        help_text=_('A detailed explanation.')
    )

    # Html expansion of descriptions
    short_description_html = property(lambda x: markdown(x.short_description))
    long_description_html = property(lambda x: markdown(x.long_description))


# We monkey patch django's Option class to make it accept a `parent_reference`
# attribute in the model's Meta class.
options.Options.parent_init_attribute = None
options.DEFAULT_NAMES = options.DEFAULT_NAMES + (
    'parent_init_attribute',
)


class MigrateMixin:
    # Migration strategy. This will be removed when the db complete its
    # migration
    migrate_attribute_conversions = {'name': 'title', 'is_active': 'live'}
    migrate_skip_attributes = {'id', 'created', 'modified', 'start', 'end'}

    @classmethod
    def migrate_extra_kwargs(cls, base):
        return {}

    @classmethod
    def migrate_post_conversions(cls, new):
        pass

    @classmethod
    def make_from_base(cls, base, commit=False):
        name_map = cls.migrate_attribute_conversions
        skip = cls.migrate_skip_attributes
        kwargs = {}

        for field in base._meta.fields:
            fname = field.name
            value = getattr(base, fname)
            if fname in skip:
                continue
            attr = name_map.get(fname, fname)
            trans = getattr(cls, 'migrate_%s_T' % attr, lambda x: x)
            kwargs[attr] = trans(value)
        kwargs.update(cls.migrate_extra_kwargs(base))

        try:
            new = cls(**kwargs)
            new.base = base
            if commit:
                new.save()
        except:
            print('init with:', kwargs)
            raise
        try:
            cls.migrate_post_conversions(new)
        except:
            new.delete()
            raise
        return new

    @classmethod
    def get_from_base(cls, base, commit=False):
        try:
            return cls.objects.get(base=base)
        except cls.DoesNotExist:
            return cls.make_from_base(base, commit=commit)

    @classmethod
    def migrate_qs(cls):
        base_model = cls._meta.get_field('base').related.model
        return base_model.objects.all()

    @classmethod
    def import_all(cls, commit=False, **kwargs):
        base_model = cls._meta.get_field('base').related.model
        base_ids = cls.objects.exclude(base__isnull=True).values_list('base', flat=True)
        qs = cls.migrate_qs().exclude(id__in=base_ids)

        if kwargs:
            qs = qs.filter(**kwargs)

        try:
            qs = qs.select_subclasses
        except AttributeError:
            pass
        else:
            qs = qs()
        print('loading: ', qs, base_model.objects.all(), base_ids)
        for obj in qs:
            try:
                print('loading', obj)
                new = cls.get_from_base(obj, commit=commit)
                print('conversion to %s complete!' % new)
            except StopIteration:
                print('skipping: %s' % obj)
