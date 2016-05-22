from codeschool.factories import *
from cs_core.factories import ProgrammingLanguageFactory
from cs_questions import models


class CodingIoAnswerKeyFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.CodingIoAnswerKey

    language = factory.SubFactory(ProgrammingLanguageFactory)
    source = "print('hello', input('who? '))"
    question = None


class CodingIoQuestionFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.CodingIoQuestion

    title = 'hello'
    short_description = 'hello world'
    long_description = 'a hello world program'
    iospec_source = 'who? <me>\nhello me'
    owner = factory.SubFactory(UserFactory)
    answer_key = factory.RelatedFactory(CodingIoAnswerKeyFactory, 'question')