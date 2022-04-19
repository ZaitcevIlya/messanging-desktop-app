import dis
from pprint import pprint


class ClientVerifier(type):
    def __init__(cls, cls_name, bases, cls_dict):
        forbidden_commands = ('accept', 'listen', 'socket')
        methods = []
        # Get methods which used in classes functions
        for func in cls_dict:
            try:
                instr = dis.get_instructions(cls_dict[func])
            except TypeError:
                pass
            else:
                for i in instr:
                    if i.opname == 'LOAD_GLOBAL':
                        if i.argval not in methods:
                            methods.append(i.argval)

        for command in forbidden_commands:
            if command in methods:
                raise TypeError(f'Method {command} does not allowed')

        if 'get_message' in methods or 'send_json_message' in methods:
            pass
        else:
            raise TypeError('There is no functions working with sockets now')
        super().__init__(cls_name, bases, cls_dict)


class ServerVerifier(type):
    def __init__(cls, cls_name, bases, cls_dict):
        forbidden_commands = ('connect',)
        # Get methods which used in classes functions - get with LOAD_GLOBAL
        global_methods = []
        # Get methods wrapped by decorators - get with LOAD_METHOD
        methods = []
        # Get attributes which used in classes functions - get with LOAD_ATTR
        attrs = []

        for func in cls_dict:
            try:
                instr = dis.get_instructions(cls_dict[func])
            except TypeError:
                pass
            else:
                for i in instr:
                    if i.opname == 'LOAD_GLOBAL':
                        if i.argval not in global_methods:
                            global_methods.append(i.argval)
                    elif i.opname == 'LOAD_METHOD':
                        if i.argval not in methods:
                            methods.append(i.argval)
                    elif i.opname == 'LOAD_ATTR':
                        if i.argval not in attrs:
                            attrs.append(i.argval)

        # print(20 * '-', 'methods', 20 * '-')
        # pprint(global_methods)
        # print(20 * '-', 'methods_2', 20 * '-')
        # pprint(methods)
        # print(20 * '-', 'attrs', 20 * '-')
        # pprint(attrs)
        # print(50 * '-')

        for command in forbidden_commands:
            if command in methods:
                raise TypeError(f'Method {command} does not allowed')

        if not ('SOCK_STREAM' in global_methods and 'AF_INET' in global_methods):
            raise TypeError('Incorrect socket initialisation')
        super().__init__(cls_name, bases, cls_dict)
