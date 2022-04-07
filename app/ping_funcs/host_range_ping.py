# 2. Написать функцию host_range_ping() (возможности которой основаны на функции из примера 1)
# для перебора ip-адресов из заданного диапазона. Меняться должен только последний октет каждого адреса.
# По результатам проверки должно выводиться соответствующее сообщение.

from ipaddress import ip_address
from host_ping import host_ping


def host_range_ping(get_list=False):
    while True:
        start_ip = input("Enter initial IP address: ")
        try:
            ipv4_start = ip_address(start_ip)
            last_oct = int(start_ip.split('.')[3])
            break
        except Exception as e:
            print(e)

    while True:
        end_ip = input("How many addresses you want to check?: ")
        if not end_ip.isnumeric():
            print("It must be a digit")
        else:
            if (last_oct + int(end_ip)) > 255+1:
                print(f"Only last octet can be changed, "
                      f"max amount of hosts: {255+1 - last_oct}")
            else:
                break
    host_list = []
    [host_list.append(str(ipv4_start + x)) for x in range(int(end_ip))]
    if not get_list:
        host_ping(host_list)
    else:
        return host_ping(host_list, True)


if __name__ == "__main__":
    host_range_ping()
