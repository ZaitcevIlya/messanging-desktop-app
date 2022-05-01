import json
import os
import sys

from common.variables import ENCODING, MAX_PACKAGE_LENGTH

sys.path.append(os.path.join(os.getcwd(), '..'))
from common.decorators import log


@log
def get_message(client):
    """
    Get and decode messages
    :param client: socket
    :return:
    """

    encoded_response = client.recv(MAX_PACKAGE_LENGTH)
    if isinstance(encoded_response, bytes):
        json_response = encoded_response.decode(ENCODING)
        response = json.loads(json_response)
        if isinstance(response, dict):
            return response
        raise ValueError
    raise ValueError


@log
def send_json_message(sock, message):
    """
    Modify dict to json and send it via provided socket
    :param sock: socket
    :param message: dict
    :return:
    """
    if not isinstance(message, dict):
        raise TypeError

    json_message = json.dumps(message)
    encoded_message = json_message.encode(ENCODING)
    sock.send(encoded_message)
