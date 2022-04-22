import os
import sys

sys.path.append('../')
from PyQt5.QtWidgets import QDialog, QLabel, QComboBox, QPushButton, QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItemModel, QStandardItem

import logging
sys.path.append(os.path.join(os.getcwd(), '../../'))
from logs import client_log_config

client_log = logging.getLogger('client_log')


class DelContactDialog(QDialog):
    def __init__(self, database):
        super().__init__()
        self.database = database

        self.setFixedSize(250, 120)
        self.setWindowTitle('Select a contact to delete')

        self.setAttribute(Qt.WA_DeleteOnClose)

        self.setModal(True)

        self.selector_label = QLabel('Select a contact to delete:', self)
        self.selector_label.setFixedSize(230, 20)
        self.selector_label.move(30, 10)

        self.selector = QComboBox(self)
        self.selector.setFixedSize(200, 20)
        self.selector.move(20, 40)

        self.selector.addItems(sorted(self.database.get_contacts()))

        self.btn_ok = QPushButton('Delete', self)
        self.btn_ok.setFixedSize(100, 30)
        self.btn_ok.move(20, 80)

        self.btn_cancel = QPushButton('Cancel', self)
        self.btn_cancel.setFixedSize(100, 30)
        self.btn_cancel.move(120, 80)
        self.btn_cancel.clicked.connect(self.close)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    from client_database import ClientDatabase
    database = ClientDatabase('test1')
    window = DelContactDialog(database)
    database.add_contact('test1')
    database.add_contact('test2')
    print(database.get_contacts())
    window.selector.addItems(sorted(database.get_contacts()))
    window.show()
    app.exec_()
