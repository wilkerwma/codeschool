import collections
from django.utils.translation import ugettext as __, ugettext_lazy as _
from codeschool import models
from codeschool.db import use_db, ask_use_db


class SourceFormatQuerySet(models.QuerySet):
    def supported(self):
        return self.filter(is_supported=True)

    def unsupported(self):
        return self.filter(is_supported=False)


class FileFormat(models.Model):
    """
    Represents a source file format.

    These can be programming languages or some specific data format.
    """

    ref = models.CharField(max_length=10, primary_key=True)
    name = models.CharField(max_length=140)
    comments = models.TextField(blank=True)
    is_binary = models.BooleanField(default=False)
    is_language = models.BooleanField(default=False)
    is_supported = models.BooleanField(default=False)
    objects = models.Manager.from_queryset(SourceFormatQuerySet)()

    def ace_mode(self):
        """
        Return the ace mode associated with the language.
        """

        return self.ref

    def pygments_mode(self):
        """
        Returns the Pygments mode associated with the language.
        """

        return self.ref


class ProgrammingLanguage(FileFormat):
    """
    Represents a programming language in codeschool.
    """

    class Meta:
        proxy = True

    objects = models.QueryManager.from_queryset(models.QuerySet)(
        is_supported=True,
        is_language=True,
    )
    unsupported = models.QueryManager(is_supported=False, is_language=True)

    def save(self, *args, **kwargs):
        self.is_language = True
        super().save(*args, **kwargs)

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


def make_initial_fixtures():
    """
    Return a string with the YAML source for the fixtures of all document
    formats.
    """

    def subs(v):
        if isinstance(v, bool):
            return str(v).lower()
        return repr(v)

    def process(L, **kwargs):
        for x in L:
            ref, _, name = x.partition(':')
            dump.append(
                '- model: cs_core.fileformat\n'
                '  pk: %r\n'
                '  fields:\n'
                '    name: %r\n' % (ref, name) +
                ''.join('    %s: %s\n' % (k, subs(v))
                          for k, v in kwargs.items())
            )

    dump = []

    # Binary formats
    process([
        'pdf:PDF',
        'rtf:Rich text format',
        'docx:Microsoft Word',
        'doc:Microsoft Word (legacy)',
        'odt:Open document text',
    ], is_binary=True)

    # Text formats
    process([
        'markdown:Markdown',
        'text:Plain Text',
        'html:HTML',
        'css:CSS',
        'latex:LaTeX',
        'tex:TeX',
    ])

    # Non-supported languages
    process([
        'ruby:Ruby',
        'java:Java',
        'javascript:Javascript',
        'perl:Perl',
        'cpp:C++11',

    ], is_language=True)

    # Supported programming languages
    process([
        'python:Python 3.5',
        'python2:Python 2.7',
        'c:C99 (gcc compiler)',
    ], is_language=True, is_supported=True)

    return '\n'.join(dump)
