from PyQt5.QtWidgets import QDialog, QLabel, QLineEdit, QPushButton, QFileDialog, QMessageBox
from PyQt5.QtCore import Qt
import os


class ConfigWindow(QDialog):
    """Server settings window"""

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.initUI()

    def initUI(self):
        # Window setup
        self.setFixedSize(365, 260)
        self.setWindowTitle('Server settings')

        # DB file path label:
        self.db_path_label = QLabel('Path to DB file: ', self)
        self.db_path_label.move(10, 10)
        self.db_path_label.setFixedSize(240, 15)

        # Actual DB file path
        self.db_path = QLineEdit(self)
        self.db_path.setFixedSize(250, 20)
        self.db_path.move(10, 30)
        self.db_path.setReadOnly(True)

        # Button for choosing DB file
        self.db_path_select = QPushButton('Explore...', self)
        self.db_path_select.move(260, 25)

        # Process the dialog window for getting DB file path
        def open_file_dialog():
            global dialog
            dialog = QFileDialog(self)
            path = dialog.getExistingDirectory()
            path = path.replace('\\', '/')
            self.db_path.clear()
            self.db_path.insert(path)

        self.db_path_select.clicked.connect(open_file_dialog)

        # DB file name label
        self.db_file_label = QLabel('DB file name: ', self)
        self.db_file_label.move(10, 68)
        self.db_file_label.setFixedSize(180, 15)

        # Enter DB file name field
        self.db_file = QLineEdit(self)
        self.db_file.move(200, 66)
        self.db_file.setFixedSize(150, 20)

        # Port number label
        self.port_label = QLabel('Server port number:', self)
        self.port_label.move(10, 108)
        self.port_label.setFixedSize(180, 15)

        # Port input field
        self.port = QLineEdit(self)
        self.port.move(200, 108)
        self.port.setFixedSize(150, 20)

        # Server address label
        self.ip_label = QLabel('Enter server address:', self)
        self.ip_label.move(10, 148)
        self.ip_label.setFixedSize(180, 15)

        # Server address label footnote
        self.ip_label_note = QLabel(' leave this field empty,\n to allow all addresses', self)
        self.ip_label_note.move(10, 168)
        self.ip_label_note.setFixedSize(500, 30)

        # Server address input field
        self.ip = QLineEdit(self)
        self.ip.move(200, 148)
        self.ip.setFixedSize(150, 20)

        # Save settings button
        self.save_btn = QPushButton('Save', self)
        self.save_btn.move(190, 220)

        # Close settings window button
        self.close_button = QPushButton('Close', self)
        self.close_button.move(275, 220)
        self.close_button.clicked.connect(self.close)

        self.show()

        self.db_path.insert(self.config['SETTINGS']['database_path'])
        self.db_file.insert(self.config['SETTINGS']['database_file'])
        self.port.insert(self.config['SETTINGS']['default_port'])
        self.ip.insert(self.config['SETTINGS']['listen_address'])
        self.save_btn.clicked.connect(self.save_server_config)

    def save_server_config(self):
        global config_window
        message = QMessageBox()
        self.config['SETTINGS']['database_path'] = self.db_path.text()
        self.config['SETTINGS']['database_file'] = self.db_file.text()
        try:
            port = int(self.port.text())
        except ValueError:
            message.warning(self, 'Error', 'Port must be a number')
        else:
            self.config['SETTINGS']['listen_address'] = self.ip.text()
            if 1023 < port < 65536:
                self.config['SETTINGS']['default_port'] = str(port)
                dir_path = os.path.dirname(os.path.realpath(__file__))
                dir_path = os.path.join(dir_path, '..')
                with open(f"{dir_path}/server.ini", 'w') as conf:
                    self.config.write(conf)
                    message.information(
                        self, 'OK', 'Settings saved')
            else:
                message.warning(
                    self, 'Error', 'Port must be a number between 1024 and 65536')
