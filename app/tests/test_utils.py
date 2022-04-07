import unittest
import os
import json
import sys

sys.path.append(os.path.join(os.getcwd(), '..'))
from common.variables import TIME, ACTION, PRESENCE, RESPONSE, USER, ACCOUNT_NAME,\
    ERROR, ENCODING, MAX_PACKAGE_LENGTH
from common.utils import send_json_message, get_message


class TestSocket:
    """
    Mock socket for testing purposes
    """
    def __init__(self, test_dict):
        self.test_dict = test_dict
        self.encoded_message = None
        self.received_message = None

    def send(self, message_to_send):
        """
        Mock "send" function of socket module
        :param message_to_send:
        :return:
        """
        json_test_message = json.dumps(self.test_dict)
        self.encoded_message = json_test_message.encode(ENCODING)
        self.received_message = message_to_send

    def recv(self, max_len):
        """
        Mock "recv" function of socket module
        :param max_len:
        :return:
        """
        json_test_message = json.dumps(self.test_dict)
        return json_test_message.encode(ENCODING)


class TestUtils(unittest.TestCase):
    def setUp(self) -> None:
        self.test_dict_send = {
            ACTION: PRESENCE,
            TIME: 5,
            USER: {
                ACCOUNT_NAME: 'Test'
            }
        }
        self.test_dict_recv_ok = {RESPONSE: 200}
        self.test_dict_recv_err = {
            RESPONSE: 400,
            ERROR: 'Bad Request'
        }

    def test_get_message_ok(self):
        test_sock_ok = TestSocket(self.test_dict_recv_ok)
        self.assertEqual(get_message(test_sock_ok), self.test_dict_recv_ok)

    def test_get_message_error(self):
        test_sock_err = TestSocket(self.test_dict_recv_err)
        self.assertEqual(get_message(test_sock_err), self.test_dict_recv_err)

    def test_send_json_message_ok(self):
        test_socket = TestSocket(self.test_dict_send)
        send_json_message(test_socket, self.test_dict_send)
        self.assertEqual(test_socket.encoded_message, test_socket.received_message)

    def test_send_json_message_error(self):
        test_socket = TestSocket(self.test_dict_send)
        send_json_message(test_socket, self.test_dict_send)
        self.assertRaises(TypeError, send_json_message, test_socket, "wrong_dictionary")
