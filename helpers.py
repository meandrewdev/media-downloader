import asyncio
import functools
import os
from os import environ, path

import i18n

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


def get_user_dir(message):
    user_dir = path.join(USERS_DIR, str(message.from_user.id))
    if not path.exists(user_dir):
        os.makedirs(user_dir)

    return user_dir


def asyncified(f):
    @functools.wraps(f)
    def inner(*args, **kwargs):
        loop = asyncio.get_running_loop()
        return loop.run_in_executor(None, lambda: f(*args, **kwargs))

    return inner
