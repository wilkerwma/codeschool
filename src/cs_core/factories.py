from codeschool.factories import *
from cs_core import models


class ProgrammingLanguageFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.ProgrammingLanguage

    ref = 'python'
    name = 'Python 3.x'
