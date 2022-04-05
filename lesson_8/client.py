import argparse
import json
import os
import sys
import threading
import time
from socket import socket, AF_INET, SOCK_STREAM
from common.variables import DEFAULT_SERVER_ADDRESS, DEFAULT_SERVER_PORT, ACTION, TIME, \
    PRESENCE, RESPONSE, USER, ACCOUNT_NAME, ERROR, SENDER, DESTINATION, MESSAGE_TEXT, MESSAGE, EXIT
from common.utils import send_json_message, get_message
from decorators import log

import logging
sys.path.append(os.path.join(os.getcwd(), '..'))
from logs import client_log_config

client_log = logging.getLogger('client_log')


@log
def message_from_server(sock, client_name):
    """Process other clients messages from server"""
    while True:
        try:
            message = get_message(sock)
            if ACTION in message and message[ACTION] == MESSAGE and \
                    SENDER in message and DESTINATION in message and MESSAGE_TEXT in message and \
                    message[DESTINATION] == client_name:
                print(f'\nGot message from client {message[SENDER]}:\n{message[MESSAGE_TEXT]}')
                client_log.info(f'Got message from client {message[SENDER]}:\n{message[MESSAGE_TEXT]}')
                print(f'Enter the command: ')
            else:
                client_log.error(f'Got error message: {message}')
        except (OSError, ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError):
            client_log.critical(f'Connection lost')
            break


@log
def create_message(sock, account_name='Guest'):
    """Ask for addresser name and message text and send data to the server"""
    to_client = input('Enter receiver username: ')
    message = input('Enter your message: ')
    message_dict = {
        ACTION: MESSAGE,
        SENDER: account_name,
        DESTINATION: to_client,
        TIME: time.time(),
        MESSAGE_TEXT: message
    }
    client_log.debug(f'Created message dict: {message_dict}')
    try:
        send_json_message(sock, message_dict)
        client_log.debug(f'Sent message to: {to_client}')
    except Exception as error:
        print(error)
        client_log.critical('Connection lost')
        sys.exit(1)


def create_exit_message(account_name):
    """Create dict with exit message"""
    return {
        ACTION: EXIT,
        TIME: time.time(),
        ACCOUNT_NAME: account_name
    }


def print_help():
    """Show client documentation"""
    print('Available commands:')
    print('message - send message. Receiver and message text handle in another place.')
    print('help - show this documentaion')
    print('exit - close connection')


@log
def user_interactions(sock, client_name):
    """Process user input"""
    print_help()
    while True:
        command = input('Enter the command: ')
        if command == 'message':
            create_message(sock, client_name)
        elif command == 'help':
            print_help()
        elif command == 'exit':
            send_json_message(sock, create_exit_message(client_name))
            print('Connection closed')
            client_log.info('Client closed connection')
            # Wait for exit message sending
            time.sleep(0.5)
            break
        else:
            print('There is no such command. Enter help - to show available commands.')


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
            ACCOUNT_NAME: account_name
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
    parser.add_argument('-n', '--name', default=None, nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    server_address = namespace.addr
    server_port = namespace.port
    client_name = namespace.name

    if not 1023 < server_port < 65536:
        client_log.critical(
            f'You run client with wrong port: {server_port}. '
            f'Allowed port are from 1024 till 65535. Bye.')
        sys.exit(1)

    return server_address, server_port, client_name


def main():
    server_address, server_port, client_name = arg_parser()

    if not client_name:
        client_name = input(f'You have to provide a name to connect to the chat.')

    print(f'Console messenger started. You logged in as: {client_name}')
    client_log.info(
        f'Client run with: server address: {server_address}, '
        f'port: {server_port}, client name: {client_name}')

    # Socket initialization
    try:
        transport = socket(AF_INET, SOCK_STREAM)
        transport.connect((server_address, server_port))
        send_json_message(transport, make_presence(client_name))
        answer = process_server_answer(get_message(transport))
        client_log.info(f'Connected to the server. Server responses: {answer}')
        print(f'Connected to the server.')
    except json.JSONDecodeError:
        client_log.error('Problem with JSON decoding.')
        sys.exit(1)
    except ConnectionRefusedError:
        client_log.critical(
            f'Can not connect to the server {server_address}:{server_port}. Server refused connection.')
        sys.exit(1)
    else:
        print(client_name)
        # If connected to the server runs receiving server messages in separated thread
        receiver = threading.Thread(target=message_from_server, args=(transport, client_name))
        receiver.daemon = True
        receiver.start()

        user_interface = threading.Thread(target=user_interactions, args=(transport, client_name))
        user_interface.daemon = True
        user_interface.start()

        print('All processes started')

        while True:
            time.sleep(1)
            if receiver.is_alive() and user_interface.is_alive():
                continue
            break


if __name__ == '__main__':
    main()
