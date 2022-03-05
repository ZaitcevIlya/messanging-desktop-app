import json
import sys
import time
from socket import socket, AF_INET, SOCK_STREAM
from common.variables import DEFAULT_SERVER_ADDRESS, DEFAULT_SERVER_PORT, ACTION, TIME, \
    PRESENCE, RESPONSE, USER, ACCOUNT_NAME
from common.utils import send_json_message, get_message


def make_presence(account_name='Guest'):
    """
    Prepare presence message
    :param account_name: str
    :return:
    """
    current_time = time.time()
    message = {
        ACTION: PRESENCE,
        TIME: current_time,
        USER: {
            ACCOUNT_NAME: account_name
        }
    }
    return message


def process_server_answer(message):
    """
    Process server answer and return status code
    :param message:
    :return:
    """
    if RESPONSE in message:
        if message[RESPONSE] == 200:
            return '200 : OK'
        return f'400 : {message[RESPONSE]}'
    return ValueError


def main():
    # Get command params
    try:
        server_address = sys.argv[1]
        server_port = int(sys.argv[2])
    except IndexError:
        server_address = DEFAULT_SERVER_ADDRESS
        server_port = DEFAULT_SERVER_PORT

    # Socket initialization
    transport = socket(AF_INET, SOCK_STREAM)
    transport.connect((server_address, server_port))
    message = make_presence()
    send_json_message(transport, message)

    try:
        server_response = get_message(transport)
        answer = process_server_answer(server_response)
        print(answer)
    except (ValueError, json.JSONDecodeError):
        print('There is an error during encoding server message')


if __name__ == '__main__':
    main()