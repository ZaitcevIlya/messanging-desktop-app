# 5. Выполнить пинг веб-ресурсов yandex.ru, youtube.com и преобразовать
# результаты из байтовового в строковый тип на кириллице.

import subprocess
import platform
import chardet

param = '-n' if platform.system().lower() == 'windows' else '-c'
args = ['ping', param, '2', 'yandex.ru']
subproc_ping = subprocess.Popen(args, stdout=subprocess.PIPE)

for line in subproc_ping.stdout:
    res = chardet.detect(line)
    line = line.decode(res['encoding']).encode('utf-8')
    print(line.decode('utf-8'))

args = ['ping', param, '2', 'youtube.com']
subproc_ping = subprocess.Popen(args, stdout=subprocess.PIPE)

for line in subproc_ping.stdout:
    res = chardet.detect(line)
    line = line.decode(res['encoding']).encode('utf-8')
    print(line.decode('utf-8'))
