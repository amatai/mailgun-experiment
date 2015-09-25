
import logging
import pymongo
import uuid
from collections import Mapping
from datetime import datetime
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
        # TODO: setup indexing here
        pass

    def add_mail(self, mail, recipient_set):
        mail['_created_at'] = datetime.utcnow()
        # create a recipient list and adjust the key, as bson docs
        # don't allow key with a '.' in it.
        mail['_recipients'] = {
            self._sanitize_for_bson(recipient): {
                'status': 'New',
                'updated': mail['_created_at'],
                'email': recipient
            } for recipient in recipient_set
        }

        # add the message to db, with a unique UUID
        # its going to be rare that we'll have UUID collision
        # its going to be extremely rare that two consecutive collisions
        result = None
        for _ in range(2):
            mail['_id'] = uuid.uuid4()
            try:
                result = self.db.mails.insert(mail, j=True)
                break
            except DuplicateKeyError:
                continue
        if not result:
            raise UnablToAddMessageError('Multiple tries led to DuplicateKeyError. Unable to add message id: {id}'.format(
                id=mail['_id']
            ))
        return self.get_mail_by_id(result)

    def get_mail_by_id(self, id):
        mail = self.db.mails.find_one({'_id': id})
        if not mail:
            raise MailLookupError('No mail with id: {id} found'.format(id=id))
        return mail

    def update_status(self, id, rcpt, status):
        rcpt = self._sanitize_for_bson(rcpt)
        update_key = '_recipients.' + rcpt + '.'
        self.db.mails.find_and_modify(
            query={'_id': id},
            update={'$set': {update_key + 'status': status, update_key + 'updated': datetime.utcnow()}},
            upsert=False,
            full_response=False,
        )

    def _sanitize_for_bson(self, email):
        return email.replace('.', '_')


class UnablToAddMessageError(Exception):
    pass


class MailLookupError(LookupError):
    pass


store = MongoStore(**config['store']['mongodb'])
