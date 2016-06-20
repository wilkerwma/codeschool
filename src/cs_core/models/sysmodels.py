from django.utils.translation import ugettext as __
from codeschool import models
from codeschool import panels


class LockedModelMixin:
    """
    Prevents model from saving changes to the database.
    """

    def save(self, *args, **kwargs):
        # We only accept changing the number of fields for existing instances
        # of locked models.
        if self.pk:
            super().save(update_fields=['numchild'])
        else:
            super().save(*args, **kwargs)


class ProfileRoot(LockedModelMixin, models.RootList):
    """
    Root page representing the parent node for all user profiles.

    This is a singleton class
    """

    class Meta:
        proxy = True

    # Wagtail admin
    subpage_types = ['cs_core.Profile']


class HiddenRoot(LockedModelMixin, models.RootList):
    """
    A page representing the site's root page
    """

    class Meta:
        proxy = True


class RogueRoot(LockedModelMixin, models.RootList):
    """
    A page representing the site's root page
    """

    class Meta:
        proxy = True


# Gets an instance from the given class root
def _root_getter(cls, **kwargs):
    try:
        return cls._instance
    except AttributeError:
        content_type = _get_content_type(cls)
        return cls.objects.get(content_type=content_type)


def profile_root():
    """
    Return the page that is root for all profile instances.
    """

    return _root_getter(ProfileRoot)


def hidden_root():
    """
    Return the page that is root for all hidden pages.
    """

    return _root_getter(HiddenRoot)


def rogue_root():
    """
    Return the page that is root for all pages with no explicit parent.
    """

    return _root_getter(RogueRoot, parent_page=hidden_root())


def init_system_pages():
    """
    Save all system pages in the db.
    """

    return dict(
        profile_root=profile_root(),
        hidden_root=hidden_root(),
        rogue_root=rogue_root(),
    )


def _get_content_type(cls):
    return models.ContentType.objects.get_for_model(
        cls, for_concrete_model=False,
    )


# Save functions as methods in the corresponding models
ProfileRoot.get_instance = staticmethod(profile_root)
HiddenRoot.get_instance = staticmethod(hidden_root)
RogueRoot.get_instance = staticmethod(rogue_root)
