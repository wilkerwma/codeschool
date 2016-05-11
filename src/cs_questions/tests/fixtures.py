import factory
from pytest_factoryboy import register
from codeschool.models import User
from cs_questions.models import


@register
class IoQuestionFactory(factory.DjangoModelFactory):
    class Meta:
        model = CodingIoQuestion

    title = 'hello'
    short_description = 'hello world'
    long_description = 'a hello world program'
    iospec_source = 'who <me>\nhello me'
    owner = factory.SubFactory(UserFactory)