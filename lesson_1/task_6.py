# 6. Создать текстовый файл test_file.txt, заполнить его тремя строками:
# «сетевое программирование», «сокет», «декоратор». Далее забыть о том,
# что мы сами только что создали этот файл и исходить из того, что перед
# нами файл в неизвестной кодировке. Задача: открыть этот файл БЕЗ ОШИБОК
# вне зависимости от того, в какой кодировке он был создан.

from chardet import detect

f = open('test.txt', 'w', encoding='utf-8')
f.writelines(['сетевое программирование\n', 'сокет\n', 'декоратор\n'])
f.close()

with open('test.txt', 'rb') as f_unknown:
    content = f_unknown.read()
encoding = detect(content)['encoding']
print('file encoding: ', encoding)

with open('test.txt', encoding=encoding) as f_known:
    for el_str in f_known:
        print(el_str, end='')
    print()




