from codeschool.fixtures import UserFactory
import factory
from pytest_factoryboy import register
from cs_auth import models


@register
class FriendshipFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.FriendshipStatus

    status = models.FriendshipStatus.STATUS_FRIEND
    owner = factory.SubFactory(UserFactory)
    other = factory.SubFactory(UserFactory)