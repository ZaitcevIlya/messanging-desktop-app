import argparse
import os
import sys
import threading

from PyQt5.QtWidgets import QApplication

from client.main_window import ClientMainWindow
from client.start_dialog import UserNameDialog
from client.transport import ClientTransport
from errors import ServerError
from common.variables import DEFAULT_SERVER_ADDRESS, DEFAULT_SERVER_PORT
from decorators import log
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

    # Create client app
    client_app = QApplication(sys.argv)

    # If app run without name ask it via dialog
    if not client_name:
        start_dialog = UserNameDialog()
        client_app.exec_()

        if start_dialog.ok_pressed:
            client_name = start_dialog.client_name.text()
            del start_dialog
        else:
            exit(0)

    client_log.info(
        f'Client run with: server address: {server_address}, '
        f'port: {server_port}, client name: {client_name}')

    # Create DB object
    database = ClientDatabase(client_name)

    # Create transport object and run it
    try:
        transport = ClientTransport(server_address, server_port, database, client_name)
    except ServerError as error:
        print(error)
        exit(1)

    transport.setDaemon(True)
    transport.start()

    # Create GUI
    main_window = ClientMainWindow(database, transport)
    main_window.make_connection(transport)
    main_window.setWindowTitle(f'Simple Chat - {client_name}')
    client_app.exec_()

    # Close transport when GUI is closed
    transport.transport_shutdown()
    transport.join()


if __name__ == '__main__':
    main()
