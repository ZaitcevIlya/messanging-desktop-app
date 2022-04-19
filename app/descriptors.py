import logging

server_log = logging.getLogger('server_log')


class Port:
    def __set__(self, instance, value):
        if not 1023 < int(value) < 65535:
            m = f'Incorrect port value {value}. Port can be only a number between 1024 and 65535.'
            server_log.critical(m)
            print(m)
            exit(1)
        instance.__dict__[self.name] = value

    def __set_name__(self, owner, name):
        self.name = name
