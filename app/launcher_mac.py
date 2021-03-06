#! /usr/bin/env python
# -*- coding: utf-8 -*-

from os import *
from subprocess import Popen
import subprocess
import time

if __name__ == '__main__':
    clients = []
    server = ''
    pathOfFile = path.dirname(__file__)
    pathServer = path.join(pathOfFile, "run_server.py")
    pathClient = path.join(pathOfFile, "run_client.py")
    pathToScriptServer = path.join(pathOfFile, "start", "startServer")
    pathToScriptClients = path.join(pathOfFile, "start", "startClient")
    print(pathClient)

    while True:
        choice = input("q - запуск сервера, w - остановка сервера, e - запуск 4 клиентов, r - остановка клиентов, t - остановить все, y - остановить все и выйти")

        if choice == "q":
            print("Запустили сервер")
            server = Popen(f"open -n -a Terminal.app '{pathServer}'", shell=True)

        elif choice == "w":
            print("Убили сервер")
            server.kill()
        elif choice == "e":
            print("Запустили клиенты")
            for i in range(1, 3):
                clients.append(Popen(f"open -n -a Terminal.app '{pathClient}'", shell=True))
                time.sleep(0.5)

        elif choice == "r":
            for i in range(len(clients)):
                print(clients[i])
                clients[i].kill()
        elif choice == "y":
            for i in range(len(clients)):
                clients[i].kill()
            server.kill()
            break
