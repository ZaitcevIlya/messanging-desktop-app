"""Constants"""
# default server address for client connection
DEFAULT_SERVER_ADDRESS = '127.0.0.1'
# default server port for client connection
DEFAULT_SERVER_PORT = 7777
# Project encoding
ENCODING = 'utf-8'
MAX_PACKAGE_LENGTH = 1024

# JIM's main keys:
ACTION = 'action'
TIME = 'time'
USER = 'user'
ACCOUNT_NAME = 'account_name'
SENDER = 'from'
DESTINATION = 'to'

# JIM's other keys:
MESSAGE = 'message'
MESSAGE_TEXT = 'message text'
PRESENCE = 'presence'
RESPONSE = 'response'
ERROR = 'error'
RESPONSE_DEFAULT_IP_ADDRESSES = 'response_default_ip_addresses'
EXIT = 'exit'

# Dicts - answers:
# 200
RESPONSE_200 = {RESPONSE: 200}
# 400
RESPONSE_400 = {
    RESPONSE: 400,
    ERROR: None
}