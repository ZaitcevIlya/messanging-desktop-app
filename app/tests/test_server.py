import unittest
import os
import sys

sys.path.append(os.path.join(os.getcwd(), '..'))
from server import process_client_message, get_params
from common.variables import TIME, ACTION, PRESENCE, RESPONSE, USER, ACCOUNT_NAME, ERROR


class TestProcessClientMessage(unittest.TestCase):
    def setUp(self) -> None:
        self.ok_dict = {
            RESPONSE: 200
        }
        self.error_dict = {
            RESPONSE: 400,
            ERROR: 'Bad Request'
        }

    def test_response_200(self):
        r = {ACTION: PRESENCE, TIME: 1.1, USER: {ACCOUNT_NAME: 'Guest'}}
        self.assertEqual(process_client_message(r), self.ok_dict)

    def test_wrong_user(self):
        """Test if passed wrong user data or didn't pass at all"""
        r = {ACTION: PRESENCE, TIME: 1.1, USER: {ACCOUNT_NAME: 'Test'}}
        self.assertEqual(process_client_message(r), self.error_dict)
        r = {ACTION: PRESENCE, TIME: 1.1}
        self.assertEqual(process_client_message(r), self.error_dict)

    def test_wrong_action(self):
        """Test if passed wrong action or didn't pass at all"""
        r = {ACTION: 'test', TIME: 1.1, USER: {ACCOUNT_NAME: 'Test'}}
        self.assertEqual(process_client_message(r), self.error_dict)
        r = {TIME: 1.1, USER: {ACCOUNT_NAME: 'Test'}}
        self.assertEqual(process_client_message(r), self.error_dict)

    def test_no_time_paased(self):
        r = {ACTION: PRESENCE, USER: {ACCOUNT_NAME: 'Test'}}
        self.assertEqual(process_client_message(r), self.error_dict)


class TestGetParams(unittest.TestCase):
    pass
