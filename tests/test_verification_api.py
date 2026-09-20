import json
import os
import sys
import tempfile
import time
import unittest
from unittest.mock import patch


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import api_server


class VerificationApiTest(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {'ECOBEE_DATA_DIR': self.tempdir.name})
        self.env.start()
        self.client = api_server.app.test_client()

    def tearDown(self):
        self.env.stop()
        self.tempdir.cleanup()

    def write_pending(self, expires_at=None):
        pending_path, _ = api_server.get_verification_paths()
        with open(pending_path, 'w') as handle:
            json.dump({
                'pending': True,
                'created_at': int(time.time()),
                'expires_at': expires_at or int(time.time()) + 60,
            }, handle)

    def test_rejects_code_without_pending_challenge(self):
        response = self.client.post('/ecobee/verification-code', json={'code': '123456'})
        self.assertEqual(409, response.status_code)

    def test_rejects_malformed_code(self):
        self.write_pending()
        response = self.client.post('/ecobee/verification-code', json={'code': '12ab56'})
        self.assertEqual(400, response.status_code)

    def test_accepts_code_only_during_pending_challenge(self):
        self.write_pending()
        response = self.client.post('/ecobee/verification-code', json={'code': '123456'})
        self.assertEqual(202, response.status_code)
        _, code_path = api_server.get_verification_paths()
        with open(code_path) as handle:
            self.assertEqual('123456', handle.read())
        self.assertEqual(0o600, os.stat(code_path).st_mode & 0o777)

    def test_expired_pending_state_is_removed(self):
        self.write_pending(expires_at=int(time.time()) - 1)
        response = self.client.get('/ecobee/verification-status')
        self.assertEqual({'pending': False}, response.get_json())

    def test_ui_shows_idle_state_without_pending_challenge(self):
        response = self.client.get('/')
        self.assertEqual(200, response.status_code)
        self.assertIn(b'No verification code is needed', response.data)
        self.assertNotIn(b'name="code"', response.data)
        self.assertEqual('no-store', response.headers['Cache-Control'])

    def test_ui_shows_code_form_during_pending_challenge(self):
        self.write_pending()
        response = self.client.get('/')
        self.assertEqual(200, response.status_code)
        self.assertIn(b'Email verification is required', response.data)
        self.assertIn(b'name="code"', response.data)

    def test_ui_rejects_malformed_code(self):
        self.write_pending()
        response = self.client.post('/', data={'code': '12ab56'})
        self.assertEqual(400, response.status_code)
        self.assertIn(b'Code must be exactly six digits', response.data)

    def test_ui_accepts_code_without_echoing_it(self):
        self.write_pending()
        response = self.client.post('/', data={'code': '123456'})
        self.assertEqual(202, response.status_code)
        self.assertIn(b'Code accepted', response.data)
        self.assertNotIn(b'123456', response.data)
        _, code_path = api_server.get_verification_paths()
        with open(code_path) as handle:
            self.assertEqual('123456', handle.read())


if __name__ == '__main__':
    unittest.main()
