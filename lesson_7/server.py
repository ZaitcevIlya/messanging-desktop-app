import os
import select
import sys
import json
import time

from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
from common.variables import ACTION, ACCOUNT_NAME, RESPONSE, PRESENCE, \
    TIME, USER, ERROR, DEFAULT_SERVER_PORT, MESSAGE, MESSAGE_TEXT, SENDER
from common.utils import get_message, send_json_message
from decorators import log

import logging
sys.path.append(os.path.join(os.getcwd(), '..'))

server_log = logging.getLogger('server_log')


@log
def process_client_message(message, messages_list, client):
    """
    Get messages from clients, check them and send response
    :param message: dict
    :param messages_list: list
    :param client: dict
    :return:
    """

    if ACTION in message and message[ACTION] == PRESENCE and TIME in message \
            and USER in message and message[USER][ACCOUNT_NAME] == 'Guest':
        send_json_message(client, {RESPONSE: 200})
        return
    elif ACTION in message and message[ACTION] == MESSAGE and \
            TIME in message and MESSAGE_TEXT in message:
        messages_list.append((message[ACCOUNT_NAME], message[MESSAGE_TEXT]))
        return
    else:
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

    print(f'Server started on port {listen_port}')
    print(f'Server accepts connections from address {listen_address}')

    clients = []
    messages = []

    # Socket initialization
    transport = socket(AF_INET, SOCK_STREAM)
    transport.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    transport.bind((listen_address, listen_port))
    transport.settimeout(0.5)
    transport.listen()

    while True:
        try:
            client, client_address = transport.accept()
        except OSError as err:
            print(err.errno)
        else:
            server_log.info(f'Client with address {client_address} connected')
            clients.append(client)

        rcv_data_lst = []
        send_data_lst = []
        err_lst = []

        try:
            if clients:
                rcv_data_lst, send_data_lst, err_lst = select.select(clients, clients, [], 0)
        except OSError:
            pass

        if rcv_data_lst:
            for client_with_message in rcv_data_lst:
                try:
                    process_client_message(get_message(client_with_message), messages, client_with_message)
                except:
                    server_log.info(f'Client {client_with_message.getpeername()} disconnected')
                    clients.remove(client_with_message)

        if messages and send_data_lst:
            message = {
                ACTION: MESSAGE,
                SENDER: messages[0][0],
                TIME: time.time(),
                MESSAGE_TEXT: messages[0][1]
            }
            del messages[0]
            for waiting_client in send_data_lst:
                try:
                    send_json_message(waiting_client, message)
                except:
                    server_log.info(f'Client {waiting_client.getpeername()} disconnected.')
                    waiting_client.close()
                    clients.remove(waiting_client)


if __name__ == '__main__':
    main()
