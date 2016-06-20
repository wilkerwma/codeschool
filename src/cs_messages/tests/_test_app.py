from cs_core.tests import *
from cs_messages import models
from cs_messages import factories as factory
from cs_messages import *

register(factory.MessageFactory)


def test_message_marked_read(db, message):
    message.mark_read()
    assert message.is_read == True
    assert message.is_active == False


def test_persistent_message_is_active_after_marked_read(db, message_factory):
    message = message_factory.create(is_persistent=True)
    message.mark_read()
    assert message.is_persistent is True
    assert message.is_read is True
    assert message.is_active is True


def test_message_to_json(db, message_factory):
    message = message_factory.create(payload='hello world!')
    json = message.to_json()
    assert set(json.keys()) ==  {
        'message_from', 'message_to', 'payload', 'status',
        'is_active', 'is_read', 'is_persistent'
    }
    assert json['message_to'] == message.message_to.username
    assert json['payload'] == 'hello world!'
    assert json['is_active'] == True
    assert json['is_read'] == False
    assert json['is_persistent'] == False


def test_utility_functions_create_messages_with_the_correct_status(db, user):
    assert debug(user, 'hello').status == models.Message.DEBUG
    assert info(user, 'hello').status == models.Message.INFO
    assert success(user, 'hello').status == models.Message.SUCCESS
    assert warning(user, 'hello').status == models.Message.WARNING
    assert error(user, 'hello').status == models.Message.ERROR

