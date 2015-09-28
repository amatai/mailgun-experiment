
import unittest


class BaseTest(unittest.TestCase):
    message_payload = {
        'from': 'someone@somewhere.com',
        'to': ['rcpt1@someplace.com', 'rcpt2@someplace2.com'],
        'message': "You've got mail!"
    }
