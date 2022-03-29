import os
import sys
import json

from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
from common.variables import ACTION, ACCOUNT_NAME, RESPONSE, PRESENCE, \
    TIME, USER, ERROR, DEFAULT_SERVER_PORT
from common.utils import get_message, send_json_message
from decorators import log

import logging
sys.path.append(os.path.join(os.getcwd(), '..'))

server_log = logging.getLogger('server_log')


@log
def process_client_message(message):
    """
    Get messages from clients, check them and send response
    :param message: dict
    :return:
    """

    if ACTION in message and message[ACTION] == PRESENCE and TIME in message \
            and USER in message and message[USER][ACCOUNT_NAME] == 'Guest':
        return {RESPONSE: 200}
    server_log.error(f'{message}')
    return {
        RESPONSE: 400,
        ERROR: 'Bad Request'
    }


def get_params():
    # Get command params
    # template: server.py -p 8888 -a 127.0.0.1
    # Port
    try:
        if '-p' in sys.argv:
            listen_port = int(sys.argv[sys.argv.index('-p') + 1])
        else:
            listen_port = DEFAULT_SERVER_PORT
        if listen_port < 1024 or listen_port > 65535:
            raise ValueError
    except IndexError:
        print('You should enter port number after -\'p\' param.')
        sys.exit(1)
    except ValueError:
        print('Port can be only a number between 1024 and 65535.')
        sys.exit(1)

    # Server address
    try:
        if '-a' in sys.argv:
            listen_address = sys.argv[sys.argv.index('-a') + 1]
        else:
            listen_address = ''
    except IndexError:
        print('You should enter server address after \'a\'param.')
        sys.exit(1)

    return listen_port, listen_address



def main():
    listen_port, listen_address = get_params()

    # Socket initialization
    transport = socket(AF_INET, SOCK_STREAM)
    transport.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    transport.bind((listen_address, listen_port))
    transport.listen()

    while True:
        client, client_address = transport.accept()
        try:
            message_from_client = get_message(client)
            server_log.info(message_from_client)
            response = process_client_message(message_from_client)
            send_json_message(client, response)
            client.close()
        except (ValueError, json.JSONDecodeError):
            server_log.error('Client message has wrong type or encoding')
            client.close()


if __name__ == '__main__':
    main()
