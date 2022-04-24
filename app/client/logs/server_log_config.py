import os
import sys

sys.path.append('../')
import logging
from logging import handlers

DIR = f'{os.getcwd()}/logs' if __name__ != '__main__' else f'{os.getcwd()}'

server_log = logging.getLogger('server_log')
server_log.setLevel(logging.DEBUG)

formatter = logging.Formatter("%(asctime)s %(levelname)-10s  %(module)15s  %(message)s")

file_handler = logging.handlers.TimedRotatingFileHandler(f'{DIR}/logging/server_log.log',
                                                         when='D', interval=1,  encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

server_log.addHandler(file_handler)


if __name__ == '__main__':
    server_log.debug('Debug msg')
    server_log.info('Info msg')
    server_log.warning('Warning msg')
    server_log.error('Error msg')
    server_log.critical(f'Crit msg')
