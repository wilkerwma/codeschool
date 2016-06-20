from cs_core.factories import *
from cs_core import factories as factory
from cs_messages import models


class MessageFactory(factory.Factory):
    class Meta:
        model = models.Message

    message_to = factory.SubFactory(factory.UserFactory)
    message_from = factory.SubFactory(factory.UserFactory)
    payload = factory.LazyAttribute(lambda x: factory.fake.text())