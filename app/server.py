import os
import select
import sys

from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR

from app.descriptors import Port
from app.metaclasses import ServerVerifier
from common.variables import ACTION, ACCOUNT_NAME, RESPONSE, PRESENCE, \
    TIME, USER, ERROR, DEFAULT_SERVER_PORT, MESSAGE, MESSAGE_TEXT, SENDER, RESPONSE_200, RESPONSE_400, EXIT, DESTINATION
from common.utils import get_message, send_json_message
from decorators import log

import logging
sys.path.append(os.path.join(os.getcwd(), '..'))

server_log = logging.getLogger('server_log')


@log
def get_params():
    """Get command params
    template: server.py -p 8888 -a 127.0.0.1
    """
    try:
        if '-p' in sys.argv:
            listen_port = int(sys.argv[sys.argv.index('-p') + 1])
        else:
            listen_port = DEFAULT_SERVER_PORT

    except IndexError:
        print('You should enter port number after -\'p\' param.')
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

    return listen_address, listen_port


class Server(metaclass=ServerVerifier):
    port = Port()

    def __init__(self, listen_address, listen_port):
        # Connection params
        self.address = listen_address
        self.port = listen_port

        # List of connected clients
        self.clients = []
        # List of messages to send
        self.messages = []
        # Names/addresses relation dictionary
        self.names = dict()

    def init_socket(self):
        print(f'Server started on port {self.port}')
        print(f'Server accepts connections from address {self.address}')
        # Socket initialization
        transport = socket(AF_INET, SOCK_STREAM)
        transport.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        transport.bind((self.address, self.port))
        transport.settimeout(0.5)

        self.sock = transport
        self.sock.listen()

    def main_loop(self):
        self.init_socket()

        while True:
            try:
                client, client_address = self.sock.accept()
            except OSError as err:
                print(err.errno)
            else:
                server_log.info(f'Client with address {client_address} connected')
                self.clients.append(client)

            rcv_data_lst = []
            send_data_lst = []
            err_lst = []

            try:
                if self.clients:
                    rcv_data_lst, send_data_lst, err_lst = select.select(self.clients, self.clients, [], 0)
            except OSError:
                pass

            if rcv_data_lst:
                for client_with_message in rcv_data_lst:
                    try:
                        self.process_client_message(get_message(client_with_message), client_with_message)
                    except Exception:
                        server_log.info(f'Client {client_with_message.getpeername()} was disconnected from the server')
                        self.clients.remove(client_with_message)

            for message in self.messages:
                try:
                    self.process_message(message,  send_data_lst)
                except:
                    server_log.info(f'Lost connection with {message[DESTINATION]}')
                    self.clients.remove(self.names[message[DESTINATION]])
                    del self.names[message[DESTINATION]]
            self.messages.clear()

    def process_message(self, message, listen_socks):
        """Process the message to the client. Got message dict, registered users, and sockets."""

        if message[DESTINATION] in self.names and self.names[message[DESTINATION]] in listen_socks:
            send_json_message(self.names[message[DESTINATION]], message)
            server_log.info(f'Send message to {message[DESTINATION]} from {message[SENDER]}.')
        elif message[DESTINATION] in self.names and self.names[message[DESTINATION]] not in listen_socks:
            raise ConnectionError
        else:
            server_log.error(f'Client {message[DESTINATION]} is not connected. '
                f'The message can not be send.')

    def process_client_message(self, message, client):
        """Get messages from clients, check them and send response"""

        if ACTION in message and message[ACTION] == PRESENCE and TIME in message and USER in message:
            # Check if such user exists. If not - register, else send answer
            if message[USER][ACCOUNT_NAME] not in self.names.keys():
                self.names[message[USER][ACCOUNT_NAME]] = client
                send_json_message(client, RESPONSE_200)
            else:
                response = RESPONSE_400
                response[ERROR] = 'User with such name already exists.'
                send_json_message(client, response)
                self.clients.remove(client)
                client.close()
            return
        # If the command is message add this message to message queue
        elif ACTION in message and message[ACTION] == MESSAGE and \
                DESTINATION in message and TIME in message and \
                SENDER in message and MESSAGE_TEXT in message:
            self.messages.append(message)
            return
        # If client closed connection
        elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message:
            self.clients.remove(self.names[message[ACCOUNT_NAME]])
            self.names[message[ACCOUNT_NAME]].close()
            del self.names[message[ACCOUNT_NAME]]
            return
        else:
            response = RESPONSE_400
            response[ERROR] = 'Bad request'
            send_json_message(client, response)
            return


def main():
    listen_address, listen_port = get_params()

    server = Server(listen_address, listen_port)
    server.main_loop()


if __name__ == '__main__':
    main()
