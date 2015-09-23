
import pymongo
from collections import Mapping
from minimailgun.config import config


class MongoStore(object):

    def __init__(self, hosts=None, database=None, username=None, password=None):
        hosts = hosts or [('127.0.0.1', None)]
        if isinstance(hosts, Mapping):
            hosts = hosts.items()
        hosts = ','.join([
            '{address}:{port}'.format(address=address, port=port or '').rstrip(':')
            for address, port in hosts
        ])

        if bool(username) != bool(password):
            raise ValueError('username and password are mutually required.')
        auth = '{username}:{password}@'.format(**locals()) if username else ''
        if not database:
            raise ValueError('database is required.')

        self.url = 'mongodb://{auth}{hosts}/{database}{options}'.format(**locals())
        self._database = database
        self._clear()

    @property
    def client(self):
        if not self._client:
            self._client = pymongo.MongoClient(self.url)
            self.setup()
        return self._client

    @property
    def db(self):
        if not self._db:
            self._db = self.client[self._database]
        return self._db

    def close(self):
        if self._client:
            self._client.close()
            self._clear()

    def _clear(self):
        self._client = None
        self._db = None

    def setup(self):
        pass

    def add_mail(self, mail):
        pass

    def get_mail_by_id(self, id):
        pass

    def find_mail_to_send(self):
        pass

    def update_mail(self, mail):
        pass

store = MongoStore(**config['store']['mongodb'])