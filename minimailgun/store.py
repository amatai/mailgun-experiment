
import logging
import pymongo
import uuid
from collections import Mapping
from pymongo.errors import DuplicateKeyError
from minimailgun.config import config


log = logging.getLogger(__name__)


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

        self.url = 'mongodb://{auth}{hosts}/{database}'.format(**locals())
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
        result = None
        for _ in range(2):
            mail['_id'] = uuid.uuid4()
            try:
                result = self.db.messages.insert_one(mail)
                break
            except DuplicateKeyError:
                continue
        if not result:
            raise UnablToAddMessageError('Multiple tries led to DuplicateKeyError. Unable to add message id: {id}'.format(
                id=mail['_id']
            ))
        return self.db.messages.find_one({'_id': result.inserted_id})

    def get_mail_by_id(self, id):
        pass

    def find_mail_to_send(self):
        pass

    def update_mail(self, mail):
        pass


class UnablToAddMessageError(Exception):
    pass


store = MongoStore(**config['store']['mongodb'])
