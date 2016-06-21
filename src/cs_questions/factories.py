from cs_core.factories import *
import cs_core.factories as factory
from cs_core.models import programming_language
from cs_questions import models


class CodingIoAnswerKeyFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.AnswerKeyItem

    language = factory.LazyAttribute(lambda x: programming_language('python'))
    source = '''
name = input('who? ')
print("hello %s!" % name)
'''


class CodingIoQuestionFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.CodingIoQuestion

    title = factory.fake_sentence(2)
    short_description = factory.fake_sentence()
    long_description = factory.fake_text()
    iospec_source = 'who? <john>\nhello john!'
    owner = factory.SubFactory(UserFactory)
    answer_key = factory.RelatedFactory(CodingIoAnswerKeyFactory, 'question')
