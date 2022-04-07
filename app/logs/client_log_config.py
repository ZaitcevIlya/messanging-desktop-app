import logging
import os

DIR = f'{os.getcwd()}/logs' if __name__ != '__main__' else f'{os.getcwd()}'

client_log = logging.getLogger('client_log')
client_log.setLevel(logging.DEBUG)

formatter = logging.Formatter("%(asctime)s %(levelname)-10s  %(module)15s  %(message)s")

file_handler = logging.FileHandler(f'{DIR}/logging/client_log.log', encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

client_log.addHandler(file_handler)


if __name__ == '__main__':
    client_log.debug('Debug msg')
    client_log.info('Info msg')
    client_log.warning('Warning msg')
    client_log.error('Error msg')
    client_log.critical('Crit msg')
