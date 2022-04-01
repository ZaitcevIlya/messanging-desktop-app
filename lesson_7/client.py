import argparse
import json
import os
import sys
import time
from socket import socket, AF_INET, SOCK_STREAM
from common.variables import DEFAULT_SERVER_ADDRESS, DEFAULT_SERVER_PORT, ACTION, TIME, \
    PRESENCE, RESPONSE, USER, ACCOUNT_NAME, ERROR, SENDER, MESSAGE_TEXT, MESSAGE
from common.utils import send_json_message, get_message
from decorators import log

import logging
sys.path.append(os.path.join(os.getcwd(), '..'))
from logs import client_log_config

client_log = logging.getLogger('client_log')


@log
def message_from_server(message):
    """Process other clients messages from server"""
    if ACTION in message and message[ACTION] == MESSAGE and SENDER in message and MESSAGE_TEXT in message:
        print(f'Got message from client {message[SENDER]}:\n{message[MESSAGE_TEXT]}')
        client_log.info(f'Got message from client {message[SENDER]}:\n{message[MESSAGE_TEXT]}')
    else:
        client_log.error(f'Got error message: {message}')


@log
def create_message(sock, account_name='Guest'):
    """Ask for message text or close connection by special command"""

    message = input('Enter your message or \'q\' to close chat: ')
    if message == 'q':
        sock.close()
        client_log.info('Client disconnected by its will.')
        print('Bye!')
        sys.exit(0)
    message_dict = {
        ACTION: MESSAGE,
        TIME: time.time(),
        ACCOUNT_NAME: account_name,
        MESSAGE_TEXT: message
    }
    client_log.debug(f'Created message dict: {message_dict}')
    return message_dict


@log
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
            ACCOUNT_NAME: 'Guest'
        }
    }
    client_log.debug(f'Presence {PRESENCE} created for client {account_name}')
    return message


@log
def process_server_answer(message):
    """
    Process server answer and return status code
    :param message:
    :return:
    """
    client_log.debug(f'Got server greetings: {message}')
    if RESPONSE in message:
        if message[RESPONSE] == 200:
            return '200 : OK'
        elif message[RESPONSE] == 400:
            return f'400 : {message[ERROR]}'
    raise ValueError


@log
def arg_parser():
    """Parse command's arguments and prepare them to use"""

    parser = argparse.ArgumentParser()
    parser.add_argument('addr', default=DEFAULT_SERVER_ADDRESS, nargs='?')
    parser.add_argument('port', default=DEFAULT_SERVER_PORT, type=int, nargs='?')
    parser.add_argument('-m', '--mode', default='listen', nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    server_address = namespace.addr
    server_port = namespace.port
    client_mode = namespace.mode

    if not 1023 < server_port < 65536:
        client_log.critical(
            f'You run client with wrong port: {server_port}. '
            f'Allowed port are from 1024 till 65535. Bye.')
        sys.exit(1)

    if client_mode not in ('listen', 'send'):
        client_log.critical(f'Wrong client mode: {client_mode}\n Allowed client modes: listen , send')
        sys.exit(1)

    return server_address, server_port, client_mode


def main():
    server_address, server_port, client_mode = arg_parser()

    print(f'Client run with: server address: {server_address}, '
        f'port: {server_port}, client mode: {client_mode}')
    client_log.info(
        f'Client run with: server address: {server_address}, '
        f'port: {server_port}, client mode: {client_mode}')

    # Socket initialization
    try:
        transport = socket(AF_INET, SOCK_STREAM)
        transport.connect((server_address, server_port))
        send_json_message(transport, make_presence())
        answer = process_server_answer(get_message(transport))
        client_log.info(f'Connected to the server. Server responses: {answer}')
        print(f'Connected to the server.')
    except json.JSONDecodeError:
        client_log.error('Problem with JSON decoding.')
        sys.exit(1)
    except ConnectionRefusedError:
        client_log.critical(
            f'Can not connect to the server  {server_address}:{server_port}. Server refused connection.')
        sys.exit(1)
    else:
        if client_mode == 'send':
            print('Set client mode to "sender".')
        else:
            print('Set client mode to "listener".')

        while True:
            if client_mode == 'send':
                try:
                    send_json_message(transport, create_message(transport))
                except (ConnectionResetError, ConnectionError, ConnectionAbortedError):
                    client_log.error(f'Connection with server {server_address} was lost.')
                    sys.exit(1)

            if client_mode == 'listen':
                try:
                    message_from_server(get_message(transport))
                except (ConnectionResetError, ConnectionError, ConnectionAbortedError):
                    client_log.error(f'Connection with server {server_address} was lost.')
                    sys.exit(1)


if __name__ == '__main__':
    main()
