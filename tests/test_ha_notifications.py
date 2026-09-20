import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from src import ha_notifications


class HomeAssistantNotificationsTest(unittest.TestCase):
    def test_reporting_available_probes_core_api(self):
        response = MagicMock()
        response.status = 200
        response.__enter__.return_value = response
        response.__exit__.return_value = False
        with patch.dict(os.environ, {'SUPERVISOR_TOKEN': 'test-token'}), patch(
            'src.ha_notifications.urllib.request.urlopen', return_value=response
        ) as urlopen:
            self.assertTrue(ha_notifications.reporting_available())
        request = urlopen.call_args.args[0]
        self.assertEqual('GET', request.method)
        self.assertEqual('Bearer test-token', request.headers['Authorization'])

    def test_skips_calls_without_supervisor_token(self):
        with patch.dict(os.environ, {}, clear=True), patch(
            'src.ha_notifications.urllib.request.urlopen'
        ) as urlopen:
            self.assertFalse(ha_notifications.report_error('Title', 'Message'))
            urlopen.assert_not_called()

    def test_reports_error_as_notification_and_system_log(self):
        response = MagicMock()
        response.status = 200
        response.__enter__.return_value = response
        response.__exit__.return_value = False
        with patch.dict(os.environ, {'SUPERVISOR_TOKEN': 'test-token'}), patch(
            'src.ha_notifications.urllib.request.urlopen', return_value=response
        ) as urlopen:
            self.assertTrue(ha_notifications.report_error('Ecobee failed', 'Open the log.'))

        self.assertEqual(2, urlopen.call_count)
        notification_request = urlopen.call_args_list[0].args[0]
        log_request = urlopen.call_args_list[1].args[0]
        self.assertTrue(notification_request.full_url.endswith(
            '/services/persistent_notification/create'
        ))
        self.assertTrue(log_request.full_url.endswith('/services/system_log/write'))
        self.assertEqual('Bearer test-token', notification_request.headers['Authorization'])
        notification_payload = json.loads(notification_request.data)
        log_payload = json.loads(log_request.data)
        self.assertEqual(
            ha_notifications.ERROR_NOTIFICATION_ID,
            notification_payload['notification_id'],
        )
        self.assertEqual('error', log_payload['level'])
        self.assertEqual('ecobee_web_control', log_payload['logger'])

    def test_verification_notification_is_actionable(self):
        response = MagicMock()
        response.status = 200
        response.__enter__.return_value = response
        response.__exit__.return_value = False
        with patch.dict(os.environ, {'SUPERVISOR_TOKEN': 'test-token'}), patch(
            'src.ha_notifications.urllib.request.urlopen', return_value=response
        ) as urlopen:
            self.assertTrue(ha_notifications.notify_verification_required())

        request = urlopen.call_args.args[0]
        payload = json.loads(request.data)
        self.assertEqual(
            ha_notifications.VERIFICATION_NOTIFICATION_ID,
            payload['notification_id'],
        )
        self.assertIn('Open Web UI', payload['message'])

    def test_success_clears_error_and_verification_notifications(self):
        response = MagicMock()
        response.status = 200
        response.__enter__.return_value = response
        response.__exit__.return_value = False
        with patch.dict(os.environ, {'SUPERVISOR_TOKEN': 'test-token'}), patch(
            'src.ha_notifications.urllib.request.urlopen', return_value=response
        ) as urlopen:
            self.assertTrue(ha_notifications.clear_notifications())

        self.assertEqual(2, urlopen.call_count)
        ids = [json.loads(call.args[0].data)['notification_id'] for call in urlopen.call_args_list]
        self.assertEqual([
            ha_notifications.ERROR_NOTIFICATION_ID,
            ha_notifications.VERIFICATION_NOTIFICATION_ID,
        ], ids)
        for call in urlopen.call_args_list:
            self.assertTrue(call.args[0].full_url.endswith(
                '/services/persistent_notification/dismiss'
            ))


if __name__ == '__main__':
    unittest.main()
