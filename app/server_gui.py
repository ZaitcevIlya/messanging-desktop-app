import sys
from PyQt5.QtWidgets import QMainWindow, QAction, qApp, QApplication, QLabel, QTableView, QDialog, QPushButton, \
    QLineEdit, QFileDialog, QMessageBox
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt
import os


# GUI - Create table QModel, to rendering withing the application window.
def gui_create_model(database):
    users_list = database.active_users_list()

    list_table = QStandardItemModel()
    list_table.setHorizontalHeaderLabels(['Username', 'IP Address', 'Port', 'Connected at'])
    for row in users_list:
        user, ip, port, time = row
        user = QStandardItem(user)
        user.setEditable(False)
        ip = QStandardItem(ip)
        ip.setEditable(False)
        port = QStandardItem(str(port))
        port.setEditable(False)
        time = QStandardItem(str(time.replace(microsecond=0)))
        time.setEditable(False)
        list_table.appendRow([user, ip, port, time])
    return list_table


# GUI - Fill history table with data.
def create_stat_model(database):
    hist_list = database.message_history()

    list_table = QStandardItemModel()
    list_table.setHorizontalHeaderLabels(
        ['Username', 'Last log in', 'Messages Sent', 'Messages Got'])
    for row in hist_list:
        user, last_seen, sent, recvd = row
        user = QStandardItem(user)
        user.setEditable(False)
        last_seen = QStandardItem(str(last_seen.replace(microsecond=0)))
        last_seen.setEditable(False)
        sent = QStandardItem(str(sent))
        sent.setEditable(False)
        recvd = QStandardItem(str(recvd))
        recvd.setEditable(False)
        list_table.appendRow([user, last_seen, sent, recvd])
    return list_table


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Button for update user list
        self.refresh_button = QAction('Update users list', self)

        # Show user history
        self.show_history_button = QAction('Users history', self)

        # Server settings button
        self.config_btn = QAction('Server settings', self)

        # Exit button
        self.exitAction = QAction('Quit', self)
        self.exitAction.setShortcut('Ctrl+Q')
        self.exitAction.triggered.connect(qApp.quit)

        # Status bar
        self.statusBar()

        # Toolbar with buttons
        self.toolbar = self.addToolBar('MainBar')
        self.toolbar.addAction(self.refresh_button)
        self.toolbar.addAction(self.show_history_button)
        self.toolbar.addAction(self.config_btn)
        self.toolbar.addAction(self.exitAction)

        # Main window proportions
        self.setFixedSize(800, 600)
        self.setWindowTitle('Messaging Server alpha release')

        self.label = QLabel('Connected users:', self)
        self.label.setFixedSize(400, 15)
        self.label.move(10, 35)

        # Connected users window
        self.active_clients_table = QTableView(self)
        self.active_clients_table.move(10, 55)
        self.active_clients_table.setFixedSize(780, 400)

        self.show()


class HistoryWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Window setup:
        self.setWindowTitle('Users statistics')
        self.setFixedSize(600, 700)
        self.setAttribute(Qt.WA_DeleteOnClose)

        # Quit button
        self.close_button = QPushButton('Close', self)
        self.close_button.move(250, 650)
        self.close_button.clicked.connect(self.close)

        # History table block
        self.history_table = QTableView(self)
        self.history_table.move(10, 10)
        self.history_table.setFixedSize(580, 620)

        self.show()


class ConfigWindow(QDialog):
    def __init__(self):
        super().__init__()
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


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.statusBar().showMessage('Test Statusbar Message')
    test_list = QStandardItemModel(main_window)
    test_list.setHorizontalHeaderLabels(['Username', 'IP Address', 'Port', 'Connected at'])
    test_list.appendRow(
        [QStandardItem('test1'), QStandardItem('192.198.0.5'), QStandardItem('23544'), QStandardItem('16:20:34')])
    test_list.appendRow(
        [QStandardItem('test2'), QStandardItem('192.198.0.8'), QStandardItem('33245'), QStandardItem('16:22:11')])
    main_window.active_clients_table.setModel(test_list)
    main_window.active_clients_table.resizeColumnsToContents()
    app.exec_()

    # ----------------------------------------------------------
    # app = QApplication(sys.argv)
    # window = HistoryWindow()
    # test_list = QStandardItemModel(window)
    # test_list.setHorizontalHeaderLabels(
    #     ['Username', 'Last log in', 'Send', 'Get'])
    # test_list.appendRow(
    #     [QStandardItem('test1'), QStandardItem('Fri Dec 12 16:20:34 2020'), QStandardItem('2'), QStandardItem('3')])
    # test_list.appendRow(
    #     [QStandardItem('test2'), QStandardItem('Fri Dec 12 16:23:12 2020'), QStandardItem('8'), QStandardItem('5')])
    # window.history_table.setModel(test_list)
    # window.history_table.resizeColumnsToContents()
    #
    # app.exec_()

    # ----------------------------------------------------------
    # app = QApplication(sys.argv)
    # dial = ConfigWindow()
    #
    # app.exec_()