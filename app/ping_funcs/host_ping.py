# 1. Написать функцию host_ping(), в которой с помощью утилиты ping
# будет проверяться доступность сетевых узлов. Аргументом функции является список,
# в котором каждый сетевой узел должен быть представлен именем хоста или ip-адресом.
# В функции необходимо перебирать ip-адреса и проверять их доступность
# с выводом соответствующего сообщения («Узел доступен», «Узел недоступен»).
# При этом ip-адрес сетевого узла должен создаваться с помощью функции ip_address().
# (Внимание! Аргументом сабпроцеса должен быть список, а не строка!!! Крайне желательно использование потоков.)

import platform
import subprocess
import threading
from ipaddress import ip_address
from pprint import pprint

result = {'Available addresses': "", "Unreachable addresses": ""}


def ping(ipv4_addr, result, get_list):
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    response = subprocess.Popen(["ping", param, '1', '-t', '1', str(ipv4_addr)], stdout=subprocess.PIPE)
    res = ''

    if response.wait() == 0:
        result['Available addresses'] += f'{ipv4_addr}\n'
        res = f'{ipv4_addr} - address is available'
    else:
        result['Unreachable addresses'] += f'{ipv4_addr}\n'
        res = f'{ipv4_addr} - address is unreachable'

    if get_list and res != '':
        return res
    print(res)


def host_ping(hosts, get_list=False):
    threads = []

    for host in hosts:
        try:
            ipv4_addr = ip_address(host)
        except ValueError as e:
            print(Exception(f'{e}'))

        thread = threading.Thread(target=ping, args=(ipv4_addr, result, get_list), daemon=True)
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

    if get_list:
        return result


if __name__ == '__main__':
    hosts_list = ['192.168.8.1', '8.8.8.8', 'yandex.ru', 'google.com', '!dasd sada',
                 '0.0.0.1', '0.0.0.2', '0.0.0.3', '0.0.0.4', '0.0.0.5',
                 '0.0.0.6', '0.0.0.7', '0.0.0.8', '0.0.0.9', '0.0.1.0']

    host_ping(hosts_list)
    pprint(result)
