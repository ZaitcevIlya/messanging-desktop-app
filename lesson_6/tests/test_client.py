import unittest
import os
import sys

sys.path.append(os.path.join(os.getcwd(), '..'))
from client import make_presence, process_server_answer
from common.variables import TIME, ACTION, PRESENCE, RESPONSE, USER, ACCOUNT_NAME, ERROR


class TestMakePresence(unittest.TestCase):
    def test_make_valid_presence(self):
        presence = make_presence()
        presence[TIME] = 2
        self.assertEqual(presence, {ACTION: PRESENCE, TIME: 2, USER: {ACCOUNT_NAME: 'Guest'}})


class TestProcessServerAnswer(unittest.TestCase):
    def test_process_200(self):
        answer = process_server_answer({RESPONSE: 200})
        self.assertEqual(answer, '200 : OK')

    def test_process_400(self):
        error_mes = 'Bad Request'
        answer = process_server_answer({RESPONSE: error_mes})
        self.assertEqual(answer, f'400 : {error_mes}')

    def test_no_response(self):
        self.assertRaises(ValueError, process_server_answer, {ERROR: 'error'})
