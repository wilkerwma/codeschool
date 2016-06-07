from django.db import models
from django.utils.translation import ugettext_lazy as _
from markdown import markdown


__all__ = [
    'CopyMixin', 'CopyableModel',
    'NamedModel',
    'DescribableModel',
]


class CopyMixin:
    """
    Mixin class that implements a safe .copy() method to create copies of
    model instances even if they are model subclasses.
    """

    def copy(self, overrides=None, commit=True):
        """Return a copy of the object. If commit=False, the copy is not saved
        to the database.

        The optional overrides dictionary defines which attributes should be
        overriden in the copied object.
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
        default='no-description',
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
