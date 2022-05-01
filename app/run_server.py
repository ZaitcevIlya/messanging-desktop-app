import argparse
import configparser
import os
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

from server.core import MessageProcessor
from server.main_window import MainWindow
from common.variables import *
from common.decorators import log
from server.server_database import ServerStorage


import logging
sys.path.append(os.path.join(os.getcwd(), '..'))

server_log = logging.getLogger('server_log')


@log
def get_params(default_address, default_port):
    """Get command params
    template: server.py -p 8888 -a 127.0.0.1
    """
    server_log.debug(
        f'Command line params parser initialization: {sys.argv}')
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=default_port, type=int, nargs='?')
    parser.add_argument('-a', default=default_address, nargs='?')
    parser.add_argument('--no_gui', action='store_true')
    namespace = parser.parse_args(sys.argv[1:])
    listen_address = namespace.a
    listen_port = namespace.p
    gui_flag = namespace.no_gui
    server_log.debug('Success!')
    return listen_address, listen_port, gui_flag


@log
def config_load():
    """Server config ini file parser."""
    config = configparser.ConfigParser()
    dir_path = os.path.dirname(os.path.realpath(__file__))
    config.read(f'{dir_path}/server.ini')
    # Fallback if there is no config file
    if 'SETTINGS' in config:
        return config
    else:
        config.add_section('SETTINGS')
        config.set('SETTINGS', 'Default_port', str(DEFAULT_SERVER_PORT))
        config.set('SETTINGS', 'Listen_Address', '')
        config.set('SETTINGS', 'Database_path', '')
        config.set('SETTINGS', 'Database_file', 'server_database.db3')
        return config


def main():
    config = config_load()

    # Get server params
    listen_address, listen_port, gui_flag = get_params(
        config['SETTINGS']['listen_address'], config['SETTINGS']['default_port']
    )

    # Init DB
    database = ServerStorage(
        os.path.join(
            config['SETTINGS']['database_path'],
            config['SETTINGS']['database_file']))

    server = MessageProcessor(listen_address, listen_port, database)
    server.daemon = True
    server.start()

    if gui_flag:
        while True:
            command = input('Type "exit" to stop the server.')
            if command == 'exit':
                server.running = False
                server.join()
                break
    else:
        server_app = QApplication(sys.argv)
        server_app.setAttribute(Qt.AA_DisableWindowContextHelpButton)
        main_window = MainWindow(database, server, config)

        # Run GUI
        server_app.exec_()

        # Stop server by window closing
        server.running = False

    # ======================================================================

    # # Create UI for the server
    # server_app = QApplication(sys.argv)
    # main_window = MainWindow()
    #
    # main_window.statusBar().showMessage('Server working')
    # main_window.active_clients_table.setModel(gui_create_model(database))
    # main_window.active_clients_table.resizeColumnsToContents()
    # main_window.active_clients_table.resizeRowsToContents()
    #
    # # Check new connection and if so updates the users list
    # def list_update():
    #     global new_connection
    #     if new_connection:
    #         main_window.active_clients_table.setModel(gui_create_model(database))
    #         main_window.active_clients_table.resizeColumnsToContents()
    #         main_window.active_clients_table.resizeRowsToContents()
    #         with conflag_lock:
    #             new_connection = False
    #
    # def show_statistics():
    #     global stat_window
    #     stat_window = HistoryWindow()
    #     stat_window.history_table.setModel(create_stat_model(database))
    #     stat_window.history_table.resizeColumnsToContents()
    #     stat_window.history_table.resizeRowsToContents()
    #     stat_window.show()
    #
    # def server_config():
    #     global config_window
    #     config_window = ConfigWindow()
    #     config_window.db_path.insert(config['SETTINGS']['database_path'])
    #     config_window.db_file.insert(config['SETTINGS']['database_file'])
    #     config_window.port.insert(config['SETTINGS']['default_port'])
    #     config_window.ip.insert(config['SETTINGS']['listen_address'])
    #     config_window.save_btn.clicked.connect(save_server_config)
    #
    # def save_server_config():
    #     global config_window
    #     message = QMessageBox()
    #     config['SETTINGS']['database_path'] = config_window.db_path.text()
    #     config['SETTINGS']['database_file'] = config_window.db_file.text()
    #     try:
    #         port = int(config_window.port.text())
    #     except ValueError:
    #         message.warning(config_window, 'ERROR', 'Port must be a number')
    #     else:
    #         config['SETTINGS']['listen_address'] = config_window.ip.text()
    #         if 1023 < port < 65536:
    #             config['SETTINGS']['default_port'] = str(port)
    #             print(port)
    #             with open('server.ini', 'w') as conf:
    #                 config.write(conf)
    #                 message.information(
    #                     config_window, 'OK', 'Settings was saved!')
    #         else:
    #             message.warning(
    #                 config_window,
    #                 'ERROR',
    #                 'Port must be a number between 1024 and 65536')
    #
    # # Update users list once per second
    # timer = QTimer()
    # timer.timeout.connect(list_update)
    # timer.start(1000)
    #
    # # Bind buttons with functions
    # main_window.refresh_button.triggered.connect(list_update)
    # main_window.show_history_button.triggered.connect(show_statistics)
    # main_window.config_btn.triggered.connect(server_config)
    #
    # # Run GUI
    # server_app.exec_()


if __name__ == '__main__':
    main()
