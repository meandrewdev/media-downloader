import json
from os import path
from urllib.parse import urlparse

from instaloader import Instaloader, Post

from helpers import asyncified

DATA_FILE = 'instagram.json'


class Instagram:
    def __init__(self, user_dir):
        self.user_dir = user_dir
        self.data = Instagram.Data.from_file(user_dir)
        pass

    @asyncified
    def login(self, username, password):
        L = Instaloader()
        L.login(username, password)

        if username in self.data.users:
            raise Exception("User already exists")

        self.data.sessions[username] = L.save_session()
        self.data.users.append(username)
        self.data.default_user = username
        self.data.write_to_file()

    @asyncified
    def get_post(self, url):
        u = urlparse(url)
        path = u.path.strip(' /')
        code = path.split("/")[-1]

        L = self.get_default_loader()
        post = Post.from_shortcode(L.context, code)

        return post

    def get_default_loader(self):
        L = Instaloader()

        if self.data.default_user:
            user = self.data.default_user
            session = self.data.sessions[user]
            L.load_session(user, session)

        return L

    class Data:
        def __init__(self, file_path, default_user='', sessions={}, users=[]):
            self.file_path = file_path
            self.default_user = default_user
            self.sessions = sessions
            self.users = users

        @classmethod
        def from_file(cls, user_dir):
            file_path = path.join(user_dir, DATA_FILE)
            if not path.exists(file_path):
                return cls(file_path)
            with open(file_path, 'r') as file:
                json_data = json.load(file)
                return cls(file_path, default_user=json_data['default_user'], sessions=json_data['sessions'], users=json_data['users'])

        def to_json(self):
            return {
                "file_path": self.file_path,
                "default_user": self.default_user,
                "sessions": self.sessions,
                "users": self.users
            }

        def write_to_file(self):
            with open(self.file_path, 'w') as file:
                json.dump(self.to_json(), file, indent=4)
