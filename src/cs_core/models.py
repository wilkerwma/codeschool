from django.utils.translation import ugettext as __, ugettext_lazy as _
from codeschool import models

supported_languages = '''
python: Python 3.x
python2: Python 2.7
pytuga: Pytuguês
c: C99 (gcc)
cpp: C++11 (g++)
'''


class ProgrammingLanguage(models.Model):
    """Represents a programming language."""

    ref = models.CharField(max_length=10, primary_key=True)
    name = models.CharField(max_length=140)
    comments = models.TextField(blank=True)
    __populated = False

    @classmethod
    def populate(cls):
        if not cls.__populated:
            for line in supported_languages.strip().splitlines():
                ref, _, name = line.partition(': ')
                cls.setdefault(ref, name)
            cls.__populated = True

    @classmethod
    def setdefault(cls, ref, *args, **kwds):
        """Create object if it does not exists."""

        try:
            return cls.objects.get(ref=ref)
        except cls.DoesNotExist:
            new = cls(ref, *args, **kwds)
            new.save()
            return new

    def __str__(self):
        return '%s (%s)' % (self.ref, self.name)

ProgrammingLanguage.populate()
