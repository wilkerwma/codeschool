import collections
from django.utils.translation import ugettext as __, ugettext_lazy as _
from codeschool import models
from codeschool.db import ask_use_db


default_languages = {
    'python': 'Python 3.x',
    'python2': 'Python 2.7',
    'pytuga': 'Pytuguês',
    'c': 'C99 (gcc)',
    'cpp': 'C++11 (g++)',
}

default_aliases = {
    'gcc': 'c',
    'g++': 'cpp',
    'c++': 'cpp',
    'python3': 'python',
}


class Base:
    def __str__(self):
        return '%s (%s)' % (self.ref, self.name)

    @classmethod
    def setdefault(cls, ref, *args, **kwds):
        """Create object if it does not exists."""

        try:
            return cls.objects.get(ref=ref)
        except cls.DoesNotExist:
            new = cls(ref, *args, **kwds)
            new.save()
            return new


class SourceFormat(Base, models.Model):
    """
    Generalizes a programming language to other non-programming based file
    formats.
    """
    # TODO: make it a base class for ProgrammingLanguage

    ref = models.CharField(max_length=10, primary_key=True)
    name = models.CharField(max_length=140)
    comments = models.TextField(blank=True)


class ProgrammingLanguage(Base, models.Model):
    """Represents a programming language."""

    ref = models.CharField(max_length=10, primary_key=True)
    name = models.CharField(max_length=140)
    comments = models.TextField(blank=True)

    @classmethod
    def get_language(cls, ref):
        """Return the programming language object from the given ref."""

        try:
            ref = default_aliases.get(ref, ref)
            return cls.objects.get(ref=ref)
        except cls.DoesNotExist:
            name = default_languages.get(ref)
            if ref is None:
                raise
            else:
                return cls.objects.create(ref=ref, name=name)

    def save(self, *args, **kwargs):
        SourceFormat.setdefault(self.ref,
                                name=self.name,
                                comments=self.comments)
        super().save(*args, **kwargs)


def get_language(ref, use_db=None):
    """Return the ProgrammingLanguage object associated with the given language
    reference.

    It creates the new object if it corresponds to a supported language that
    does not exist in the database.

    Args:
        ref:
            The short primary key reference to the language (e.g., 'python',
            'c', 'c++', etc)
        use_db:
            If False, it does not touch the database and return an unsaved
            language object. The default behavior is to touch the database
            unless it is running in a :func:`codeschool.dbg.no_db` block.
    """

    if ask_use_db(use_db):
        return ProgrammingLanguage.get_language(ref)
    else:
        try:
            ref = default_aliases.get(ref, ref)
            return ProgrammingLanguage(
                ref=ref,
                name=default_languages[ref]
            )
        except KeyError:
            raise ProgrammingLanguage.DoesNotExist(ref)


def get_languages(use_db=None):
    """Return an iterator with all languages in alphabetical order."""

    # Get initial list
    if ask_use_db(use_db):
        L = ProgrammingLanguage.objects.all()
    else:
        L = []

    # Fill it with all supported languages not present in the list
    refs = {lang.ref for lang in L}
    for ref, name in default_languages.items():
        if ref not in refs:
            L.append(get_language(ref, use_db))

    # Sort alphabetically by reference
    return sorted(L, key=lambda x: x.ref)
