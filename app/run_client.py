import argparse
import os
import sys
import threading
from Crypto.PublicKey import RSA
from PyQt5.QtWidgets import QApplication, QMessageBox

from client.main_window import ClientMainWindow
from client.start_dialog import UserNameDialog
from client.transport import ClientTransport
from common.errors import ServerError
from common.variables import DEFAULT_SERVER_ADDRESS, DEFAULT_SERVER_PORT
from common.decorators import log
from client.client_database import ClientDatabase

import logging
sys.path.append(os.path.join(os.getcwd(), '..'))

client_log = logging.getLogger('client_log')

sock_lock = threading.Lock()
database_lock = threading.Lock()

@log
def arg_parser():
    """Parse command's arguments and prepare them to use"""
    parser = argparse.ArgumentParser()
    parser.add_argument('addr', default=DEFAULT_SERVER_ADDRESS, nargs='?')
    parser.add_argument('port', default=DEFAULT_SERVER_PORT, type=int, nargs='?')
    parser.add_argument('-n', '--name', default=None, nargs='?')
    parser.add_argument('-p', '--password', default='', nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    server_address = namespace.addr
    server_port = namespace.port
    client_name = namespace.name
    client_password = namespace.password

    if not 1023 < server_port < 65536:
        client_log.critical(
            f'You run client with wrong port: {server_port}. '
            f'Allowed port are from 1024 till 65535. Bye.')
        sys.exit(1)

    return server_address, server_port, client_name, client_password


def main():
    server_address, server_port, client_name, client_password = arg_parser()
    client_log.debug('Args loaded')

    # Create client app
    client_app = QApplication(sys.argv)

    # If app run without name ask it via dialog
    start_dialog = UserNameDialog()
    if not client_name or not client_password:
        client_app.exec_()

        if start_dialog.ok_pressed:
            client_name = start_dialog.client_name.text()
            client_password = start_dialog.client_password.text()
            client_log.debug(f'Using USERNAME = {client_name}, PASSWD = {client_password}.')
        else:
            exit(0)

    client_log.info(
        f'Client run with: server address: {server_address}, '
        f'port: {server_port}, client name: {client_name}')

    # Get keys from file if there is no one, generate it
    dir_path = os.path.dirname(os.path.realpath(__file__))
    key_file = os.path.join(dir_path, f'{client_name}.key')
    if not os.path.exists(key_file):
        keys = RSA.generate(2048, os.urandom)
        with open(key_file, 'wb') as key:
            key.write(keys.export_key())
    else:
        with open(key_file, 'rb') as key:
            keys = RSA.import_key(key.read())

    client_log.debug("Keys successfully loaded.")

    # Create DB object
    database = ClientDatabase(client_name)

    # Create transport object and run it
    try:
        transport = ClientTransport(server_address, server_port, database, client_name, client_password, keys)
        client_log.debug('Transport is ready')
    except ServerError as error:
        message = QMessageBox()
        message.critical(start_dialog, 'Server Error', error.text)
        exit(1)
    transport.setDaemon(True)
    transport.start()

    # Delete dialog
    del start_dialog

    # Create GUI
    main_window = ClientMainWindow(database, transport, keys)
    main_window.make_connection(transport)
    main_window.setWindowTitle(f'Simple Chat - {client_name}')
    client_app.exec_()

    # Close transport when GUI is closed
    transport.transport_shutdown()
    transport.join()


if __name__ == '__main__':
    main()
