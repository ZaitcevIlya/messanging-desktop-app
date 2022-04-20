import configparser
import os
import select
import sys
import threading

from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QMessageBox

from server_gui import MainWindow, gui_create_model, HistoryWindow, create_stat_model, ConfigWindow
from descriptors import Port
from metaclasses import ServerVerifier
from common.variables import ACTION, ACCOUNT_NAME, RESPONSE, PRESENCE, \
    TIME, USER, ERROR, DEFAULT_SERVER_PORT, MESSAGE, MESSAGE_TEXT, SENDER, RESPONSE_200, RESPONSE_400, EXIT, \
    DESTINATION, GET_CONTACTS, RESPONSE_202, LIST_INFO, ADD_CONTACT, REMOVE_CONTACT, USERS_REQUEST
from common.utils import get_message, send_json_message
from decorators import log
from server_database import ServerStorage

import logging
sys.path.append(os.path.join(os.getcwd(), '..'))

server_log = logging.getLogger('server_log')

# Indicator of new connection, need to reduce amount of DB calls
conflag_lock = threading.Lock()
new_connection = False

@log
def get_params(default_address, default_port):
    """Get command params
    template: server.py -p 8888 -a 127.0.0.1
    """
    try:
        if '-p' in sys.argv:
            listen_port = int(sys.argv[sys.argv.index('-p') + 1])
        else:
            listen_port = default_port
    except IndexError:
        print('You should enter port number after -\'p\' param.')
        sys.exit(1)

    # Server address
    try:
        if '-a' in sys.argv:
            listen_address = sys.argv[sys.argv.index('-a') + 1]
        else:
            listen_address = default_address
    except IndexError:
        print('You should enter server address after \'a\'param.')
        sys.exit(1)

    return listen_address, listen_port


class Server(threading.Thread, metaclass=ServerVerifier):
    port = Port()

    def __init__(self, listen_address, listen_port, database):
        # Connection params
        self.address = listen_address
        self.port = listen_port

        self.database = database

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

        while True:
            try:
                client, client_address = self.sock.accept()
            except OSError:
                pass
            else:
                server_log.info(f'Client with address {client_address} connected')
                self.clients.append(client)

            rcv_data_lst = []
            send_data_lst = []
            err_lst = []

            try:
                if self.clients:
                    rcv_data_lst, send_data_lst, err_lst = select.select(self.clients, self.clients, [], 0)
            except OSError as err:
                server_log.error(f'Something went wrong withing socket work: {err}')

            if rcv_data_lst:
                for client_with_message in rcv_data_lst:
                    try:
                        self.process_client_message(get_message(client_with_message), client_with_message)
                    except OSError:
                        server_log.info(f'Client {client_with_message.getpeername()} was disconnected from the server')
                        for name in self.names:
                            if self.names[name] == client_with_message:
                                self.database.user_logout(name)
                                del self.names[name]
                                break
                        self.clients.remove(client_with_message)

            for message in self.messages:
                try:
                    self.process_message(message, send_data_lst)
                except:
                    server_log.info(f'Lost connection with {message[DESTINATION]}')
                    self.clients.remove(self.names[message[DESTINATION]])
                    self.database.user_logout(message[DESTINATION])
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
        global new_connection

        if ACTION in message and message[ACTION] == PRESENCE and TIME in message and USER in message:
            # Check if such user exists. If not - register, else send answer
            if message[USER][ACCOUNT_NAME] not in self.names.keys():
                self.names[message[USER][ACCOUNT_NAME]] = client
                client_ip, client_port = client.getpeername()
                self.database.user_login(message[USER][ACCOUNT_NAME], client_ip, client_port)
                send_json_message(client, RESPONSE_200)
                with conflag_lock:
                    new_connection = True
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
            self.database.process_message(message[SENDER], message[DESTINATION])
            return
        # If client closed connection
        elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message:
            self.database.user_logout(message[ACCOUNT_NAME])
            self.clients.remove(self.names[message[ACCOUNT_NAME]])
            self.names[message[ACCOUNT_NAME]].close()
            del self.names[message[ACCOUNT_NAME]]
            with conflag_lock:
                new_connection = True
            return
        # Request for contacts list
        elif ACTION in message and message[ACTION] == GET_CONTACTS and USER in message and \
                self.names[message[USER]] == client:
            response = RESPONSE_202
            response[LIST_INFO] = self.database.get_contacts(message[USER])
            send_json_message(client, response)
        # Request for Add contact
        elif ACTION in message and message[ACTION] == ADD_CONTACT and ACCOUNT_NAME in message and USER in message \
                and self.names[message[USER]] == client:
            self.database.add_contact(message[USER], message[ACCOUNT_NAME])
            send_json_message(client, RESPONSE_200)
        # Request for Remove contact
        elif ACTION in message and message[ACTION] == REMOVE_CONTACT and ACCOUNT_NAME in message and USER in message \
                and self.names[message[USER]] == client:
            self.database.remove_contact(message[USER], message[ACCOUNT_NAME])
            send_json_message(client, RESPONSE_200)
        # Request for Registered users
        elif ACTION in message and message[ACTION] == USERS_REQUEST and ACCOUNT_NAME in message \
                and self.names[message[ACCOUNT_NAME]] == client:
            response = RESPONSE_202
            response[LIST_INFO] = [user[0] for user in self.database.users_list()]
            send_json_message(client, response)
        else:
            response = RESPONSE_400
            response[ERROR] = 'Bad request'
            send_json_message(client, response)
            return


def main():
    config = configparser.ConfigParser()

    dir_path = os.path.dirname(os.path.realpath(__file__))
    config.read(f'{dir_path}/server.ini')

    # Get server params
    listen_address, listen_port = get_params(
        config['SETTINGS']['listen_address'], config['SETTINGS']['default_port']
    )

    # Init DB
    database = ServerStorage(
        os.path.join(
            config['SETTINGS']['database_path'],
            config['SETTINGS']['database_file']))

    server = Server(listen_address, listen_port, database)
    server.daemon = True
    server.start()

    # Create UI for the server
    server_app = QApplication(sys.argv)
    main_window = MainWindow()

    main_window.statusBar().showMessage('Server working')
    main_window.active_clients_table.setModel(gui_create_model(database))
    main_window.active_clients_table.resizeColumnsToContents()
    main_window.active_clients_table.resizeRowsToContents()

    # Check new connection and if so updates the users list
    def list_update():
        global new_connection
        if new_connection:
            main_window.active_clients_table.setModel(gui_create_model(database))
            main_window.active_clients_table.resizeColumnsToContents()
            main_window.active_clients_table.resizeRowsToContents()
            with conflag_lock:
                new_connection = False

    def show_statistics():
        global stat_window
        stat_window = HistoryWindow()
        stat_window.history_table.setModel(create_stat_model(database))
        stat_window.history_table.resizeColumnsToContents()
        stat_window.history_table.resizeRowsToContents()
        stat_window.show()

    def server_config():
        global config_window
        config_window = ConfigWindow()
        config_window.db_path.insert(config['SETTINGS']['database_path'])
        config_window.db_file.insert(config['SETTINGS']['database_file'])
        config_window.port.insert(config['SETTINGS']['default_port'])
        config_window.ip.insert(config['SETTINGS']['listen_address'])
        config_window.save_btn.clicked.connect(save_server_config)

    def save_server_config():
        global config_window
        message = QMessageBox()
        config['SETTINGS']['database_path'] = config_window.db_path.text()
        config['SETTINGS']['database_file'] = config_window.db_file.text()
        try:
            port = int(config_window.port.text())
        except ValueError:
            message.warning(config_window, 'ERROR', 'Port must be a number')
        else:
            config['SETTINGS']['listen_address'] = config_window.ip.text()
            if 1023 < port < 65536:
                config['SETTINGS']['default_port'] = str(port)
                print(port)
                with open('server.ini', 'w') as conf:
                    config.write(conf)
                    message.information(
                        config_window, 'OK', 'Settings was saved!')
            else:
                message.warning(
                    config_window,
                    'ERROR',
                    'Port must be a number between 1024 and 65536')

    # Update users list once per second
    timer = QTimer()
    timer.timeout.connect(list_update)
    timer.start(1000)

    # Bind buttons with functions
    main_window.refresh_button.triggered.connect(list_update)
    main_window.show_history_button.triggered.connect(show_statistics)
    main_window.config_btn.triggered.connect(server_config)

    # Run GUI
    server_app.exec_()


if __name__ == '__main__':
    main()
