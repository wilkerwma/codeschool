from cs_core.factories import *
import cs_core.factories as factory
from cs_core.models import get_language
from cs_questions import models


class CodingIoAnswerKeyFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.CodingIoAnswerKey

    language = factory.LazyAttribute(lambda x: get_language('python'))
    source = "print('hello', input('who? '))"


class CodingIoQuestionFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.CodingIoQuestion

    title = 'hello'
    short_description = 'hello world'
    long_description = 'a hello world program'
    iospec_source = 'who? <me>\nhello me'
    owner = factory.SubFactory(UserFactory)
    answer_key = factory.RelatedFactory(CodingIoAnswerKeyFactory, 'question')
