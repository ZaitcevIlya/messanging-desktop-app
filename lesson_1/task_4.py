# 4. Преобразовать слова «разработка», «администрирование», «protocol», «standard» из строкового представления
#  в байтовое и выполнить обратное преобразование (используя методы encode и decode).

arr = ["разработка", "администрирование", "protocol", "standard"]

for w in arr:
    try:
        en_str = w.encode('utf-8')
        print(f'{en_str} - {type(en_str)}')
        de_str = en_str.decode('utf-8')
        print(f'{de_str} - {type(de_str)}')
    except Exception:
        print(w, 'cannot be byte type')
