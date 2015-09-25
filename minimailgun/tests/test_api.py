import copy
import uuid
from mock import patch

from minimailgun import api
from minimailgun.store import MailLookupError
from minimailgun.tests.base import BaseTest


class TestMiniMailgunAPI(BaseTest):
    def setUp(self):
        self.client = api.app.test_client()

    def test_get_no_uuid_404(self):
        rv = self.client.get('/mail/abc')
        self.assertEqual(rv.status_code, 404)

    @patch.object(api.store, 'get_mail_by_id', side_effect=MailLookupError)
    def test_get_bad_uuid_404(self, get_mail_mock):
        rv = self.client.get('/mail/{}'.format(uuid.uuid4()))
        self.assertEqual(rv.status_code, 404)

    def test_post_content_type(self):
        rv = self.client.post('/mail', data=self.message_payload, headers={'Content-Type': 'text/plain'})
        self.assertEqual(rv.status_code, 415)

    def test_post_accept_mimetype(self):
        rv = self.client.post(
            '/mail',
            data=self.message_payload,
            headers={'Content-Type': 'application/json', 'Accept': 'text/plain'}
        )
        self.assertEqual(rv.status_code, 406)

    def test_post_input_from(self):
        message_copy = copy.deepcopy(self.message_payload)
        message_copy.pop('from')
        rv = self.client.post(
            '/mail',
            data=message_copy,
            headers={'Content-Type': 'application/json', 'Accept': 'application/json'}
        )
        self.assertEqual(rv.status_code, 400)

    def test_post_recipient(self):
        message_copy = copy.deepcopy(self.message_payload)
        message_copy.pop('to')
        rv = self.client.post(
            '/mail',
            data=message_copy,
            headers={'Content-Type': 'application/json', 'Accept': 'application/json'}
        )
        self.assertEqual(rv.status_code, 400)
