import hmac
import os
import binascii
import select
import sys
import threading
import logging

from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR

from common.descriptors import Port
from common.variables import *
from common.utils import get_message, send_json_message

sys.path.append(os.path.join(os.getcwd(), '..'))

server_log = logging.getLogger('server_log')


class MessageProcessor(threading.Thread):
    port = Port()

    def __init__(self, listen_address, listen_port, database):
        # Connection params
        self.address = listen_address
        self.port = listen_port
        self.database = database

        self.receiver_sockets = None
        self.listener_sockets = None
        self.error_sockets = None
        # Server start/stop flag
        self.running = True
        # List of connected clients
        self.clients = []
        # List of messages to send
        self.messages = []
        # Names/addresses relation dictionary
        self.names = dict()

        super().__init__()

    def init_socket(self):
        print(f'Server started on port {self.port}')
        print(f'Server accepts connections from address {self.address}')
        # Socket initialization
        transport = socket(AF_INET, SOCK_STREAM)
        transport.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        transport.bind((self.address, int(self.port)))
        transport.settimeout(0.5)

        self.sock = transport
        self.sock.listen()

    def run(self):
        self.init_socket()

        while self.running:
            try:
                client, client_address = self.sock.accept()
            except OSError:
                pass
            else:
                server_log.info(f'Client with address {client_address} connected')
                self.clients.append(client)

            # Check for waiting users
            try:
                if self.clients:
                    self.receiver_sockets, self.listener_sockets, self.error_sockets = select.select(
                        self.clients, self.clients, [], 0)
            except OSError as err:
                server_log.error(f'Something went wrong withing socket work: {err}')

            # Receive messages, if error disconnect user
            if self.receiver_sockets:
                for client_with_message in self.receiver_sockets:
                    try:
                        self.process_client_message(get_message(client_with_message), client_with_message)
                    except OSError:
                        server_log.info(f'Client {client_with_message.getpeername()} was disconnected from the server')
                        self.remove_client(client_with_message)

    def remove_client(self, client):
        for name in self.names:
            if self.names[name] == client:
                self.database.user_logout(name)
                del self.names[name]
                break
        self.clients.remove(client)
        client.close()

    def try_send_msg_or_close(self, client, response):
        try:
            send_json_message(client, response)
        except OSError:
            self.remove_client(client)

    def process_message(self, message):
        """Process the message to the client. Got message dict, registered users, and sockets."""

        if message[DESTINATION] in self.names and self.names[message[DESTINATION]] in self.listener_sockets:
            try:
                send_json_message(self.names[message[DESTINATION]], message)
                server_log.info(f'Send message to {message[DESTINATION]} from {message[SENDER]}.')
            except OSError:
                self.remove_client(message[DESTINATION])

        elif message[DESTINATION] in self.names and self.names[message[DESTINATION]] not in self.listener_sockets:
            server_log.error(f'Connection with client {message[DESTINATION]} was lost. Delivery is impossible.')
            self.remove_client(self.names[message[DESTINATION]])
        else:
            server_log.error(f'Client {message[DESTINATION]} is not registered at the server. '
                f'The message cannot be send.')

    # todo implement decorator @login required later
    def process_client_message(self, message, client):
        """Get messages from clients, check them and send response"""
        # global new_connection

        if ACTION in message and message[ACTION] == PRESENCE and TIME in message and USER in message:
            # Check if such user exists. If not - register, else send answer
            self.authorize_user(message, client)
        # If the command is message send this message
        elif ACTION in message and message[ACTION] == MESSAGE and \
                DESTINATION in message and TIME in message and \
                SENDER in message and MESSAGE_TEXT in message and \
                self.names[message[SENDER]] == client:
            if message[DESTINATION] in self.names:
                self.database.process_message(message[SENDER], message[DESTINATION])
                self.process_message(message)
                response = RESPONSE_200
                self.try_send_msg_or_close(client, response)
            else:
                response = RESPONSE_400
                response[ERROR] = 'User did not registered on server'
                try:
                    send_json_message(client, response)
                except OSError:
                    pass
            return

        # Client leave the chat
        elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message and\
                self.names[message[ACCOUNT_NAME]] == client:
            self.remove_client(client)
        
        # Request for contacts list
        elif ACTION in message and message[ACTION] == GET_CONTACTS and USER in message and \
                self.names[message[USER]] == client:
            response = RESPONSE_202
            response[LIST_INFO] = self.database.get_contacts(message[USER])
            self.try_send_msg_or_close(client, response)

        # Request for Add contact
        elif ACTION in message and message[ACTION] == ADD_CONTACT and ACCOUNT_NAME in message and USER in message \
                and self.names[message[USER]] == client:
            self.database.add_contact(message[USER], message[ACCOUNT_NAME])
            response = RESPONSE_200
            self.try_send_msg_or_close(client, response)

        # Request for Remove contact
        elif ACTION in message and message[ACTION] == REMOVE_CONTACT and ACCOUNT_NAME in message and USER in message \
                and self.names[message[USER]] == client:
            self.database.remove_contact(message[USER], message[ACCOUNT_NAME])
            response = RESPONSE_200
            self.try_send_msg_or_close(client, response)

        # Request for Registered users
        elif ACTION in message and message[ACTION] == USERS_REQUEST and ACCOUNT_NAME in message \
                and self.names[message[ACCOUNT_NAME]] == client:
            response = RESPONSE_202
            response[LIST_INFO] = [user[0] for user in self.database.users_list()]
            self.try_send_msg_or_close(client, response)

        # If it's a public key request
        elif ACTION in message and message[ACTION] == PUBLIC_KEY_REQUEST and ACCOUNT_NAME in message:
            response = RESPONSE_511
            response[DATA] = self.database.get_pubkey(message[ACCOUNT_NAME])

            if response[DATA]:
                self.try_send_msg_or_close(client, response)
            else:
                response = RESPONSE_400
                response[ERROR] = 'There is not pub key for this user'
                self.try_send_msg_or_close(client, response)
        else:
            response = RESPONSE_400
            response[ERROR] = 'Bad request'
            self.try_send_msg_or_close(client, response)

    def authorize_user(self, message, client):
        server_log.debug(f'Start auth process for {message[USER]}')
        if message[USER][ACCOUNT_NAME] in self.names.keys():
            response = RESPONSE_400
            response[ERROR] = 'User with such name already exists.'
            server_log.error('User with such name already exists.')
            self.try_send_msg_or_close(client, response)
        elif not self.database.check_user(message[USER][ACCOUNT_NAME]):
            response = RESPONSE_400
            response[ERROR] = 'There is no user with such name.'
            server_log.error('There is no user with such name.')
            self.try_send_msg_or_close(client, response)
        else:
            server_log.debug('Correct username, starting passwd check.')
            message_auth = RESPONSE_511
            random_str = binascii.hexlify(os.urandom(64))
            message_auth[DATA] = random_str.decode('ascii')
            hash = hmac.new(self.database.get_hash(message[USER][ACCOUNT_NAME]), random_str, 'MD5')
            digest = hash.digest()
            server_log.debug(f'Auth message: {message_auth}')
            try:
                send_json_message(client, message_auth)
                ans = get_message(client)
            except OSError as err:
                server_log.debug('Error in auth, data:', exc_info=err)
                client.close()
                return

            client_digest = binascii.a2b_base64(ans[DATA])
            if RESPONSE in ans and ans[RESPONSE] == 511 and \
                    hmac.compare_digest(digest, client_digest):
                self.names[message[USER][ACCOUNT_NAME]] = client
                client_ip, client_port = client.getpeername()
                try:
                    send_json_message(client, RESPONSE_200)
                except OSError:
                    self.remove_client(message[USER][ACCOUNT_NAME])

                self.database.user_login(
                    message[USER][ACCOUNT_NAME],
                    client_ip,
                    client_port,
                    message[USER][PUBLIC_KEY])
            else:
                response = RESPONSE_400
                response[ERROR] = 'Wrong password'
                try:
                    send_json_message(client, response)
                except OSError:
                    pass
                self.clients.remove(client)
                client.close()

    def service_update_lists(self):
        for client in self.names:
            try:
                send_json_message(self.names[client], RESPONSE_205)
            except OSError:
                self.remove_client(self.names[client])
