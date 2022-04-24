import json
import os
import sys
import threading
import socket
import time

from PyQt5.QtCore import QObject, pyqtSignal

from common.utils import send_json_message, get_message
from common.variables import *
from errors import ServerError

import logging
sys.path.append(os.path.join(os.getcwd(), '..'))
from logs import client_log_config

client_log = logging.getLogger('client_log')
socket_lock = threading.Lock()


class ClientTransport(threading.Thread, QObject):
    new_message = pyqtSignal(str)
    connection_lost = pyqtSignal()
    
    def __init__(self, ip_address, port, database, username):
        threading.Thread.__init__(self)
        QObject.__init__(self)
        # DB object
        self.database = database
        self.username = username
        # Socket to work with server
        self.transport = None

        self.connection_init(ip_address, port)

        try:
            self.user_list_update()
            self.contacts_list_update()
        except OSError as err:
            if err.errno:
                client_log.critical('Connection lost')
                raise ServerError('Connection with server lost')
            client_log.error('Timeout of connection during user list update')
        except json.JSONDecodeError as err:
            client_log.critical('Connection lost')
            raise ServerError('Connection with server lost')
        self.running = True

    def connection_init(self, ip, port):
        self.transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.transport.settimeout(5)

        # Try to connect 5 times at least
        connected = False
        for i in range(5):
            client_log.info(f'Connection attempt №{i + 1}')
            try:
                self.transport.connect((ip, port))
            except (OSError, ConnectionRefusedError):
                pass
            else:
                connected = True
                break
            time.sleep(1)

        if not connected:
            client_log.critical('Cannot connect to the server')
            raise ServerError('Cannot connect to the server')

        client_log.debug('Connected to the server')

        try:
            with socket_lock:
                send_json_message(self.transport, self.create_presence())
                self.process_server_ans(get_message(self.transport))
        except (OSError, json.JSONDecodeError):
            client_log.critical('Connection lost')
            raise ServerError('Connection lost')

        client_log.info('Connected to the server')

    def create_presence(self):
        message = {
            ACTION: PRESENCE,
            TIME: time.time(),
            USER: {
                ACCOUNT_NAME: self.username
            }
        }
        client_log.debug(f'Presence {PRESENCE} created for client {self.username}')
        return message

    def process_server_ans(self, message):
        client_log.debug(f'Parse server answer: {message}')

        if RESPONSE in message:
            if message[RESPONSE] == 200:
                return
            elif message[RESPONSE] == 400:
                raise ServerError(f'{message[ERROR]}')
            else:
                client_log.debug(f'Unknown response code {message[RESPONSE]}')

        # If there is a message add to DB and send signal about new message
        elif ACTION in message \
                and message[ACTION] == MESSAGE \
                and SENDER in message \
                and DESTINATION in message \
                and MESSAGE_TEXT in message \
                and message[DESTINATION] == self.username:
            client_log.debug(f'Got message from user {message[SENDER]}:'
                         f'{message[MESSAGE_TEXT]}')
            self.database.save_message(message[SENDER], 'in', message[MESSAGE_TEXT])
            self.new_message.emit(message[SENDER])

    def contacts_list_update(self):
        client_log.debug(f'Request user\'s contacts list {self.name}')
        req = {
            ACTION: GET_CONTACTS,
            TIME: time.time(),
            USER: self.username
        }
        client_log.debug(f'Request {req} is ready')
        with socket_lock:
            send_json_message(self.transport, req)
            ans = get_message(self.transport)
        client_log.debug(f'Server answer received {ans}')
        if RESPONSE in ans and ans[RESPONSE] == 202:
            for contact in ans[LIST_INFO]:
                self.database.add_contact(contact)
        else:
            client_log.error('Cannot update user contacts list')

    def user_list_update(self):
        client_log.debug(f'Request known users list {self.username}')
        req = {
            ACTION: USERS_REQUEST,
            TIME: time.time(),
            ACCOUNT_NAME: self.username
        }
        with socket_lock:
            send_json_message(self.transport, req)
            ans = get_message(self.transport)
        if RESPONSE in ans and ans[RESPONSE] == 202:
            self.database.add_users(ans[LIST_INFO])
        else:
            client_log.error('Cannot update users list')

    def add_contact(self, contact):
        client_log.debug(f'Create contact {contact}')
        req = {
            ACTION: ADD_CONTACT,
            TIME: time.time(),
            USER: self.username,
            ACCOUNT_NAME: contact
        }
        with socket_lock:
            send_json_message(self.transport, req)
            self.process_server_ans(get_message(self.transport))

    def remove_contact(self, contact):
        client_log.debug(f'Delete contact {contact}')
        req = {
            ACTION: REMOVE_CONTACT,
            TIME: time.time(),
            USER: self.username,
            ACCOUNT_NAME: contact
        }
        with socket_lock:
            send_json_message(self.transport, req)
            self.process_server_ans(get_message(self.transport))

    def transport_shutdown(self):
        self.running = False
        message = {
            ACTION: EXIT,
            TIME: time.time(),
            ACCOUNT_NAME: self.username
        }
        with socket_lock:
            try:
                send_json_message(self.transport, message)
            except OSError:
                pass
        client_log.debug('Transport is finishing its work.')
        time.sleep(0.5)

    def send_message(self, to, message):
        message_dict = {
            ACTION: MESSAGE,
            SENDER: self.username,
            DESTINATION: to,
            TIME: time.time(),
            MESSAGE_TEXT: message
        }
        client_log.debug(f'Message dict is prepared: {message_dict}')

        # Wait until socket is free
        with socket_lock:
            send_json_message(self.transport, message_dict)
            self.process_server_ans(get_message(self.transport))
            client_log.info(f'Send message from user {to}')

    def run(self):
        client_log.debug('Start process - Message receiver')
        while self.running:
            # Wait for a sec and try to get a socket again, need for freeing socket for message sender
            time.sleep(1)
            with socket_lock:
                try:
                    self.transport.settimeout(0.5)
                    message = get_message(self.transport)
                except OSError as err:
                    if err.errno:
                        client_log.critical(f'Connection lost')
                        self.running = False
                        self.connection_lost.emit()
                except (ConnectionError, ConnectionAbortedError,
                        ConnectionResetError, json.JSONDecodeError, TypeError):
                    client_log.debug(f'Connection lost')
                    self.running = False
                    self.connection_lost.emit()
                else:
                    client_log.debug(f'Got message from server: {message}')
                    self.process_server_ans(message)
                finally:
                    self.transport.settimeout(5)
