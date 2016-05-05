import pytest
import pytest_django
import pytest_selenium
from codeschool.testing import fake
from sulfur import Driver


@pytest.fixture
def ui(selenium, live_server):
    return Driver(selenium, base_url=live_server.url, wait=1)


@pytest.fixture
def dom(ui):
    return ui.dom


@pytest.mark.django_db
def test_user_can_create_account_and_login(fake, ui, dom):
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
    ui.click('button')
    assert ui.wait_title_contains(username, timeout=2)


