import pytest
from codeschool.testing import *
from codeschool.models import User


@pytest.mark.django_db
def test_existing_user_can_login(ui, dom, user_with_password, password):
    ui.get()
    dom.id_identification = user_with_password.username
    dom.id_password = password
    ui.click('button.primary')
    full_name = user_with_password.get_full_name()
    assert full_name in ui.title


@pytest.mark.django_db
def _test_user_can_create_account_and_login(ui, dom):
    ui.get()
    assert 'Codeschool' in ui.title

    # Fill sign up form
    password = fake.password()
    ui.click('a[href="#signup"]')
    dom.id_first_name = fake.first_name()
    dom.id_last_name = fake.last_name()
    dom.id_username = username = fake.user_name()
    dom.id_email = fake.email()
    dom.id_password1 = password
    dom.id_password2 = password
    ui.click('button.primary')
    user = User.objects.get(username=username)
    full_name = user.get_full_name()
    assert full_name in ui.title


