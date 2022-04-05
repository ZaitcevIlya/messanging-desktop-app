import os
import select
import sys
import json
import time

from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
from common.variables import ACTION, ACCOUNT_NAME, RESPONSE, PRESENCE, \
    TIME, USER, ERROR, DEFAULT_SERVER_PORT, MESSAGE, MESSAGE_TEXT, SENDER, RESPONSE_200, RESPONSE_400, EXIT, DESTINATION
from common.utils import get_message, send_json_message
from decorators import log

import logging
sys.path.append(os.path.join(os.getcwd(), '..'))

server_log = logging.getLogger('server_log')


@log
def process_client_message(message, messages_list, client, clients, names):
    """
    Get messages from clients, check them and send response
    :param message: dict
    :param messages_list: list
    :param client: dict
    :param clients:
    :param names:
    :return:
    """

    if ACTION in message and message[ACTION] == PRESENCE and TIME in message and USER in message:
        # Check if such user exists. If not - register, else send answer
        if message[USER][ACCOUNT_NAME] not in names.keys():
            names[message[USER][ACCOUNT_NAME]] = client
            send_json_message(client, RESPONSE_200)
        else:
            response = RESPONSE_400
            response[ERROR] = 'User with such name already exists.'
            send_json_message(client, response)
            clients.remove(client)
            client.close()
        return
    # If the command is message add this message to message queue
    elif ACTION in message and message[ACTION] == MESSAGE and \
            DESTINATION in message and TIME in message and \
            SENDER in message and MESSAGE_TEXT in message:
        messages_list.append(message)
        return
    # If client closed connection
    elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message:
        clients.remove(names[message[ACCOUNT_NAME]])
        names[message[ACCOUNT_NAME]].close()
        del names[message[ACCOUNT_NAME]]
        return
    else:
        response = RESPONSE_400
        response[ERROR] = 'Bad request'
        send_json_message(client, response)
        return


@log
def process_message(message, names, listen_socks):
    """Process the message to the client. Got message dict, registered users, and sockets.
    :param message:
    :param names:
    :param listen_socks:
    :return:
    """

    if message[DESTINATION] in names and names[message[DESTINATION]] in listen_socks:
        send_json_message(names[message[DESTINATION]], message)
        server_log.info(f'Send message to {message[DESTINATION]} '
                    f'from {message[SENDER]}.')
    elif message[DESTINATION] in names and names[message[DESTINATION]] not in listen_socks:
        raise ConnectionError
    else:
        server_log.error(
            f'Client {message[DESTINATION]} is not connected. '
            f'The message can not be send.')


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

    # Socket initialization
    transport = socket(AF_INET, SOCK_STREAM)
    transport.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    transport.bind((listen_address, listen_port))
    transport.settimeout(0.5)

    clients = []
    messages = []
    # Dict with usernames and related sockets
    names = dict()

    transport.listen(5)

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
                    process_client_message(get_message(client_with_message),
                                           messages, client_with_message, clients, names)
                except Exception:
                    server_log.info(f'Client {client_with_message.getpeername()} was disconnected from the server')
                    clients.remove(client_with_message)

        for i in messages:
            try:
                process_message(i, names, send_data_lst)
            except Exception:
                server_log.info(f'Lost connection with {i[DESTINATION]}')
                clients.remove(names[i[DESTINATION]])
                del names[i[DESTINATION]]
        messages.clear()


if __name__ == '__main__':
    main()
