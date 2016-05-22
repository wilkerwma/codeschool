from codeschool.factories import *
from cs_auth.models import FriendshipStatus


class FriendshipStatusFactory(factory.DjangoModelFactory):
    class Meta:
        model = FriendshipStatus

    status = FriendshipStatus.STATUS_FRIEND
    owner = factory.SubFactory(UserFactory)
    other = factory.SubFactory(UserFactory)
