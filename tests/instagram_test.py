import json
import unittest

from instagram import Instagram


class TestInstagramLogin(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.instagram = Instagram('./tests')

    async def test_real_login(self):
        with open('./tests/user.json', 'r') as file:
            user_data = json.load(file)
        username = user_data['username']
        password = user_data['password']

        await self.instagram.login(username, password, True)
        self.assertEqual(self.instagram.data.default_user, username)

        is_logged = await self.instagram.check_login()
        self.assertTrue(is_logged)

    async def test_get_post(self):
        url = 'https://www.instagram.com/reel/C5v2r49o_8Z/?igsh=N2NiczQzZWVhMzE1'
        post = await self.instagram.get_post(url)
        self.assertIsNotNone(post)
        self.assertEqual(post.shortcode, 'C5v2r49o_8Z')
        self.assertEqual(post.typename, 'GraphVideo')


if __name__ == '__main__':
    unittest.main()
