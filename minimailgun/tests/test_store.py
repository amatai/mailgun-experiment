
import mongomock
import copy
import uuid
from mock import patch

from minimailgun import store
from minimailgun.tests.base import BaseTest

store_kwargs = {'hosts': {'localhost': 27017}, 'database': 'test_mm'}
test_store = store.MongoStore(**store_kwargs)

saved_uuid = uuid.uuid4()


class TestMongoStore(BaseTest):
    def setUp(self):
        test_store._clear()
        test_store._client = mongomock.MongoClient(**store_kwargs)

    def test_add_mail(self):
        stored_message = test_store.add_mail(copy.deepcopy(self.message_payload), set(self.message_payload['to']))
        stored_message.pop('_id', None)
        stored_message.pop('_created_at', None)
        stored_message.pop('_recipients', None)
        self.assertDictEqual(stored_message, self.message_payload)

    def test_add_mail_adds_attributes(self):
        stored_message = test_store.add_mail(copy.deepcopy(self.message_payload), set(self.message_payload['to']))
        self.assertIn('_id', stored_message)
        self.assertIn('_created_at', stored_message)
        self.assertIn('_recipients', stored_message)

    @patch.object(store.uuid, 'uuid4', return_value=saved_uuid)
    def test_raises_unable_to_add(self, uuid4):
        test_store.add_mail(copy.deepcopy(self.message_payload), set(self.message_payload['to']))
        with self.assertRaises(store.UnablToAddMessageError):
            test_store.add_mail(copy.deepcopy(self.message_payload), set(self.message_payload['to']))

    def test_get_mail_by_id_raises(self):
        with self.assertRaises(store.MailLookupError):
            test_store.get_mail_by_id(saved_uuid)

    def test_get_mail_by_id(self):
        message = test_store.add_mail(copy.deepcopy(self.message_payload), set(self.message_payload['to']))
        stored_message = test_store.get_mail_by_id(message['_id'])
        self.assertDictEqual(message, stored_message)
