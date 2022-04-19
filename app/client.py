import argparse
import json
import os
import sys
import threading
import time
from socket import socket, AF_INET, SOCK_STREAM

from errors import ServerError
from metaclasses import ClientVerifier
from common.variables import DEFAULT_SERVER_ADDRESS, DEFAULT_SERVER_PORT, ACTION, TIME, \
    PRESENCE, RESPONSE, USER, ACCOUNT_NAME, ERROR, SENDER, DESTINATION, MESSAGE_TEXT, MESSAGE, EXIT, ADD_CONTACT, \
    GET_CONTACTS, LIST_INFO, USERS_REQUEST, REMOVE_CONTACT
from common.utils import send_json_message, get_message
from decorators import log
from client_database import ClientDatabase

import logging
sys.path.append(os.path.join(os.getcwd(), '..'))
from logs import client_log_config

client_log = logging.getLogger('client_log')

sock_lock = threading.Lock()
database_lock = threading.Lock()


class ClientSender(threading.Thread, metaclass=ClientVerifier):
    def __init__(self, account_name, sock, database):
        self.account_name = account_name
        self.sock = sock
        self.database = database
        super().__init__()

    def create_exit_message(self):
        """Create dict with exit message"""
        return {
            ACTION: EXIT,
            TIME: time.time(),
            ACCOUNT_NAME: self.account_name
        }

    def create_message(self):
        """Ask for addresser name and message text and send data to the server"""
        to_client = input('Enter receiver username: ')
        message = input('Enter your message: ')

        # Check that receiver is exists
        with database_lock:
            if not self.database.check_user(to_client):
                client_log.error(f'Attempt to send message to unregistered user {to_client}')
                return

        message_dict = {
            ACTION: MESSAGE,
            SENDER: self.account_name,
            DESTINATION: to_client,
            TIME: time.time(),
            MESSAGE_TEXT: message
        }
        client_log.debug(f'Created message dict: {message_dict}')

        # Save message for history
        with database_lock:
            self.database.save_message(self.account_name, to_client, message)

        # Waiting for socket to be free to send message
        with sock_lock:
            try:
                send_json_message(self.sock, message_dict)
                client_log.info(f'Message to user {to_client} is sent')
            except OSError as err:
                if err.errno:
                    client_log.critical('Connection with server lost')
                    exit(1)
                else:
                    client_log.error('Have not sent the message. Connection timeout')

    def run(self):
        self.print_help()

        while True:
            command = input('Enter the command: ')
            if command == 'message':
                self.create_message()
            elif command == 'help':
                self.print_help()
            elif command == 'exit':
                with sock_lock:
                    try:
                        send_json_message(self.sock, self.create_exit_message())
                    except Exception as e:
                        print(e)
                        pass
                    print('Connection is closing.')
                    client_log.info('Connection closed by user\'s command.')
                # Wait for exit message sending
                time.sleep(0.5)
                break
            elif command == 'contacts':
                with database_lock:
                    contacts_list = self.database.get_contacts()
                for contact in contacts_list:
                    print(contact)
            elif command == 'edit':
                self.edit_contacts()
            elif command == 'history':
                self.print_history()
            else:
                print('There is no such command. Enter help - to show available commands.')

    def print_help(self):
        """Show client documentation"""
        print('Available commands:')
        print('message - send message. Receiver and message text handle in another place.')
        print('contacts - show user\'s contacts list')
        print('edit - edit user contacts list')
        print('history - show user\'s messages history')
        print('help - show this documentaion')
        print('exit - close connection')

    def print_history(self):
        ask = input('Show incoming messages - "in", outgoing - "out", all - just press "Enter": ')
        with database_lock:
            if ask == 'in':
                history_list = self.database.get_history(to_who=self.account_name)
                for message in history_list:
                    print(f'\nMessage from user: {message[0]} '
                          f'at {message[3]}:\n{message[2]}')
            elif ask == 'out':
                history_list = self.database.get_history(from_who=self.account_name)
                for message in history_list:
                    print(f'\nMessage to user: {message[1]} '
                          f'at {message[3]}:\n{message[2]}')
            else:
                history_list = self.database.get_history()
                for message in history_list:
                    print(f'\nMessage from user: {message[0]},'
                          f' to user {message[1]} '
                          f'at {message[3]}\n{message[2]}')

    def edit_contacts(self):
        ans = input('Enter "del" to delete some contact.\n Enter "add" to add some new contact: ')
        if ans == 'del':
            edit = input('Enter the name of the contact you want to delete: ')
            with database_lock:
                if self.database.check_contact(edit):
                    self.database.del_contact(edit)
                else:
                    client_log.error('Attempting to delete the non-existing contact.')
        elif ans == 'add':
            edit = input('Enter the name of the contact you want to add: ')
            if self.database.check_user(edit):
                with database_lock:
                    self.database.add_contact(edit)
                with sock_lock:
                    try:
                        add_contact(self.sock, self.account_name, edit)
                    except Exception:
                        client_log.error('Could not send data to the server.')


class ClientReader(threading.Thread, metaclass=ClientVerifier):
    def __init__(self, account_name, sock, database):
        self.account_name = account_name
        self.sock = sock
        self.database = database
        super().__init__()

    def run(self):
        """Process other clients messages from server"""
        while True:
            time.sleep(1)
            with sock_lock:
                try:
                    message = get_message(self.sock)
                except OSError as err:
                    if err.errno:
                        client_log.critical(f'Connection lost')
                        break
                except (ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError) as err:
                    print('this error: ', err)
                    client_log.critical(f'Connection lost')
                    break
                else:
                    if ACTION in message and message[ACTION] == MESSAGE and \
                            SENDER in message and DESTINATION in message and MESSAGE_TEXT in message and \
                            message[DESTINATION] == self.account_name:

                        with database_lock:
                            try:
                                self.database.save_message(message[SENDER], self.account_name,
                                                           message[MESSAGE_TEXT])
                            except Exception as e:
                                print(e)
                                client_log.error('Failed connection to DB')

                        print(f'\nGot message from client {message[SENDER]}:\n{message[MESSAGE_TEXT]}')
                        client_log.info(f'Got message from client {message[SENDER]}:\n{message[MESSAGE_TEXT]}')
                        print(f'Enter the command: ')
                    else:
                        client_log.error(f'Got error message: {message}')


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
def make_presence(account_name):
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


def contacts_list_request(sock, name):
    client_log.debug(f'Request for contact list for user {name}')
    req = {
        ACTION: GET_CONTACTS,
        TIME: time.time(),
        USER: name
    }
    client_log.debug(f'Created request {req}')
    send_json_message(sock, req)
    ans = get_message(sock)
    client_log.debug(f'Received response {ans}')
    if RESPONSE in ans and ans[RESPONSE] == 202:
        return ans[LIST_INFO]
    else:
        raise ServerError


def add_contact(sock, username, contact):
    client_log.debug(f'Creating of the contact {contact}')
    req = {
        ACTION: ADD_CONTACT,
        TIME: time.time(),
        USER: username,
        ACCOUNT_NAME: contact
    }
    send_json_message(sock, req)
    ans = get_message(sock)
    if RESPONSE in ans and ans[RESPONSE] == 200:
        pass
    else:
        raise Exception('New contact was not created. Server error.')
    print('New contact created.')


def user_list_request(sock, username):
    client_log.debug(f'Request of known users {username}')
    req = {
        ACTION: USERS_REQUEST,
        TIME: time.time(),
        ACCOUNT_NAME: username
    }
    send_json_message(sock, req)
    ans = get_message(sock)
    if RESPONSE in ans and ans[RESPONSE] == 202:
        return ans[LIST_INFO]
    else:
        raise Exception


def remove_contact(sock, username, contact):
    client_log.debug(f'Request for deleting contact {contact}')
    req = {
        ACTION: REMOVE_CONTACT,
        TIME: time.time(),
        USER: username,
        ACCOUNT_NAME: contact
    }
    send_json_message(sock, req)
    ans = get_message(sock)
    if RESPONSE in ans and ans[RESPONSE] == 200:
        pass
    else:
        raise Exception('Contact deleting failed')
    print('Contact was deleted successfully')


def database_load(sock, database, username):
    try:
        users_list = user_list_request(sock, username)
    except Exception:
        client_log.error('Request of known users failed.')
    else:
        database.add_users(users_list)

    try:
        contacts_list = contacts_list_request(sock, username)
    except Exception:
        client_log.error('Request of user contacts failed.')
    else:
        for contact in contacts_list:
            database.add_contact(contact)


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
        transport.settimeout(1)

        transport.connect((server_address, server_port))
        send_json_message(transport, make_presence(client_name))
        answer = process_server_answer(get_message(transport))
        client_log.info(f'Connected to the server. Server responses: {answer}')
        print(f'Connected to the server.')
    except json.JSONDecodeError:
        client_log.error('Problem with JSON decoding.')
        sys.exit(1)
    except ConnectionRefusedError as err:
        client_log.critical(
            f'Can not connect to the server {server_address}:{server_port}. Server refused connection.')
        client_log.error(err)
        sys.exit(1)
    else:
        database = ClientDatabase(client_name)
        database_load(transport, database, client_name)

        module_sender = ClientSender(client_name, transport, database)
        module_sender.daemon = True
        module_sender.start()
        client_log.info('Client processing')

        # If connected to the server runs receiving server messages in separated thread
        module_receiver = ClientReader(client_name, transport, database)
        module_receiver.daemon = True
        module_receiver.start()

        while True:
            time.sleep(1)
            if module_receiver.is_alive() and module_sender.is_alive():
                continue
            break


if __name__ == '__main__':
    main()
