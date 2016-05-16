from codeschool.fixtures import *
from cs_questions.models import CodingIoQuestion


@register
class IoQuestionFactory(factory.DjangoModelFactory):
    class Meta:
        model = CodingIoQuestion

    title = 'hello'
    short_description = 'hello world'
    long_description = 'a hello world program'
    iospec_source = 'who <me>\nhello me'
    owner = factory.SubFactory(UserFactory)
