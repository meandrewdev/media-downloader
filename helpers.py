import asyncio
import functools
import os
from os import environ, path

import i18n
from instaloader import LoginRequiredException

USERS_DIR = environ.get("USERS_DIR", "users")
TRANSLATIONS_DIR = environ.get("TRANSLATIONS_DIR", "translations")

i18n.set('file_format', 'yaml')
i18n.set('filename_format', '{locale}.{format}')
i18n.set('skip_locale_root_data', True)
i18n.load_path.append(TRANSLATIONS_DIR)
i18n.set('locale', 'en')
i18n.set('fallback', 'en')

if not path.exists(USERS_DIR):
    os.makedirs(USERS_DIR)


# get user settings and session directory by tg bot user id from tg bit message
def get_user_dir(message):
    user_dir = path.join(USERS_DIR, str(message.from_user.id))
    if not path.exists(user_dir):
        os.makedirs(user_dir)

    return user_dir


# decorator to make a function async
def asyncified(f):
    @functools.wraps(f)
    async def inner(*args, **kwargs):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: f(*args, **kwargs))
    return inner


# decorator to check is user logged in
def must_login(func):
    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        if not self.data.default_user:
            raise LoginRequiredException("User not found")

        if not self.data.sessions.get(self.data.default_user):
            raise LoginRequiredException("User not found")

        if not self.data.sessions[self.data.default_user]:
            raise LoginRequiredException("User not found")

        if not await self.check_login():
            raise LoginRequiredException("Check login failed")

        result = await func(self, *args, **kwargs)
        return result

    return wrapper
