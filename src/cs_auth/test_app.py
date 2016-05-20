from codeschool.testing import *
from cs_auth.factories import *

# Fixtures
register(FriendshipStatusFactory)


class TestURLs(URLBaseTester):
    public_urls = [
        '/',
        '/accounts/login',
        '/accounts/signout',
    ]
    login_urls = [
        '/accounts/{user.username}/edit',
        '/accounts/{user.username}/password',
        '/accounts/{user.username}/email',
    ]

    @pytest.mark.django_db
    def test_can_login(self, client, user_with_password, password):
        url = '/accounts/login'
        response = client.post(url, {
            'identification': user_with_password.username,
            'password': password,
            'action': 'signin',
        })
        self.expect(200, 400, response, url)
