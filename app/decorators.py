import os
import sys
import inspect

sys.path.append(os.path.join(os.getcwd(), '..'))
import logging
from logs import client_log_config, server_log_config


def log(func_to_logging):
    """Decorator function"""
    def wrap(*args, **kwargs):
        logger_name = 'server_log' if 'server.py' in sys.argv[0] else 'client_log'
        logger = logging.getLogger(logger_name)
        f = func_to_logging(*args, **kwargs)

        logger.debug(
            f'{func_to_logging.__name__} was called with params {args}, {kwargs} '
            f'from module {func_to_logging.__module__} '
            f'from function {inspect.stack()[1][3]}'
        )
        return f
    return wrap

