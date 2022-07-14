# Парсер книг с сайта tululu.org

Скрипт скачивает книги и обложку к ним с онлайн-библиотеки tululu.org.

## Как установить

1. Скачайте проект:<br>

```commandline
git clone https://github.com/NankuF/online_library.git
```

2. Перейдите в директорию:

```commandline
cd online_library
```
3. Создайте виртуальное окружение:<br>

```commandline
python -m venv venv
```

4. Активируйте виртуальное окружение:<br>
Unix
```commandline
. ./venv/bin/activate
```
Windows
```commandline
. .\venv\Scripts\activate
```
5. Установите зависимости:<br>

```commandline
pip install -r requirements.txt
```

5. Запустите скрипт:<br>
`-s, --start_id` - с какого id начать скачивание книг.<br>
`-e, --end_id` - на каком id закончить скачивание книг.<br>
```commandline
python main.py -s 10 -e 20
```