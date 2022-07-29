# Парсер книг с сайта tululu.org

Скрипт скачивает книги и обложку к ним с онлайн-библиотеки [tululu.org](https://tululu.org).
Так же есть возможность собрать книги в json, не скачивая их на жесткий диск.

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
`--start_page` - с какой страницы начать скачивание книг.<br>
`--end_page` - какую страницу с книгами скачать последней.<br>
`--dest_folder` - путь к каталогу с результатами парсинга: картинкам, книгам, JSON.<br>
`--skip_imgs` - не скачивать картинки.<br>
`--skip_txt` - не скачивать книги.<br>
`--json_path` - указать свой путь к *.json файлу с результатами.<br>

Варианты:<br>
Скачать одну страницу с книгами - первую. Файлы, изображения и json-файлы сохранить в папку "parse_result".
Txt файлы в "parse_result/books", обложки в "parse_result/images", json в корень "parse_result".
```commandline
python main.py --start_page 1 --end_page 1
```
Скачать две страницы с книгами - первую и вторую.
```commandline
python main.py --start_page 1 --end_page 2
```
Скачать все страницы с книгами.
```commandline
python main.py --start_page 1
```
Скачать с 60 страницы до конца каталога.
```commandline
python main.py --start_page 60
```
Скачать 2 страницы, книги и обложки поместить в папку "result/books" и "result/images", а json-файлы в папку "json".
```commandline
python main.py --start_page 1 --end_page 2 --dest_folder "result" --json_path "json"
```
Скачать 5 страницы, книги и обложки **не скачивать**, а json-файлы сохранить в папке "json".
```commandline
python main.py --start_page 1 --end_page 5 --skip_txt --skip_imgs --json_path "json"
```