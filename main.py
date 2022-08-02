import argparse
import json
import os
import time
import traceback
import urllib.parse
from pathlib import *

import requests
from bs4 import BeautifulSoup
from lxml import etree
from pathvalidate import sanitize_filename
from requests import HTTPError
from requests.sessions import Session

from parse_tululu_category import get_all_links, save_book_links


def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--start_page', type=int, default=1, help='с какой страницы начать скачивание книг.')
    parser.add_argument('--end_page', type=int, default=1, help='какую страницу с книгами скачать последней.')
    parser.add_argument('--dest_folder', default='parse_result',
                        help='путь к каталогу с результатами парсинга: картинкам, книгам, JSON.')
    parser.add_argument('--skip_imgs', action='store_true', help='не скачивать картинки.')
    parser.add_argument('--skip_txt', action='store_true', help='не скачивать книги.')
    parser.add_argument('--json_path', default='parse_result', help=' указать свой путь к *.json файлу с результатами')

    return parser


def fetch_filename(url: str) -> str:
    """Получить имя файла из url, без расширения"""
    clear_path = urllib.parse.unquote(urllib.parse.urlsplit(url).path)
    return os.path.splitext(clear_path)[0].split('/')[-1]


def check_for_redirect(response):
    """
    Проверяет был ли редирект.

    :param response: ответ сервера.
    """
    if response.history:
        raise HTTPError('Битая ссылка.')


def download_txt(url, filename, session: Session, folder: Path) -> Path:
    """Функция для скачивания текстовых файлов.

    Args:
        url (str): Ссылка на текст, который хочется скачать.
        filename (str): Имя файла, с которым сохранять.
        folder (Path): Папка, куда сохранять.
        session (Session) - сессия http-соединения.
    Returns:
        Path: Путь до файла, куда сохранён текст.
    """
    dir_ = Path(folder) / 'books'
    Path.mkdir(dir_, exist_ok=True)
    file_extension = fetch_filename(url)
    filename = f'{sanitize_filename(filename)}.{file_extension}'
    filepath = Path(dir_, filename)

    resp = session.get(url)
    resp.raise_for_status()
    check_for_redirect(resp)

    with open(filepath, 'wb') as file:
        file.write(resp.content)
    return filepath


def download_image(url: str, session: Session, folder: Path) -> Path:
    """Скачать изображение"""
    dir_ = Path(folder) / 'images'
    Path.mkdir(dir_, exist_ok=True)
    filename = Path(url).name
    filepath = Path(dir_, filename)

    resp = session.get(url)
    resp.raise_for_status()
    check_for_redirect(resp)

    with open(filepath, 'wb') as file:
        file.write(resp.content)

    return filepath


def parse_book_page(response) -> dict:
    """
    Возвращает словарь со всеми данными о книге: название, автор и т.д.

    :param response: ответ сервера.
    :return: словарь с собранными данными о книге.
    """
    soup = BeautifulSoup(response.text, 'lxml')
    tree = etree.HTML(response.content)

    title, author = [text.strip() for text in soup.select_one('#content h1').text.split('::')]
    if tree.xpath("//td/a[contains(@href,'/txt.php')]"):
        download_book_url = tree.xpath("//td/a[contains(@href,'/txt.php')]")[0].attrib['href']
    else:
        raise IndexError('Отсутствует ссылка на скачивание книги.')
    download_book_url = urllib.parse.urljoin(response.url, download_book_url)
    image = soup.select_one('.bookimage a img[src]').attrs['src']
    image_url = urllib.parse.urljoin(response.url, image)
    comments = [tag.text for tag in soup.select('div.texts .black')]
    genres = [tag.text for tag in soup.select('span.d_book a')]

    return {
        'title': title,
        'author': author,
        'download_book_url': download_book_url,
        'image_url': image_url,
        'comments': comments,
        'genres': genres,
    }


def save_links_collection(url: str, session, start_page: int, end_page: int, folder: Path) -> dict:
    """
    Проверяет есть ли ссылки для скачивания книг в директории. Если ссылок нет - скачивает и сохраняет их.

    :param url: ссылка на каталог с книгами.
    :param session: объект сессии.
    :param start_page: страница с которой начать скачивать ссылки на книги.
    :param end_page: какую страницу с книгами скачать последней.
    :param folder: куда сохранить файл.
    :return: словарь с ссылками на книги.
    """
    book_collection_path = Path(folder) / 'links_collection.json'
    last_page = end_page if end_page else 'последнюю'
    message = f'Скачиваю ссылки на книги c {start_page} по {last_page} страницы.'
    if not Path(book_collection_path).exists():
        Path.mkdir(folder, exist_ok=True)
        print(message)
        books_collections = get_all_links(url, start_page=start_page, end_page=end_page, session=session)
        save_book_links(books_collections, book_collection_path)
    else:
        with open(book_collection_path, 'r') as file:
            books = json.load(file)
        if not books.get(str(end_page)) or not books.get(str(start_page)):
            print(message)
            books_collections = get_all_links(url, start_page=start_page, end_page=end_page, session=session)
            save_book_links(books_collections, book_collection_path)

    with open(book_collection_path, 'r') as file:
        books = json.load(file)
    return books


def main():
    connection_error_timeout = 300
    count_reconnect = 1
    parser = create_parser()
    namespace = parser.parse_args()
    start_page = namespace.start_page
    end_page = namespace.end_page
    dest_folder = Path(namespace.dest_folder) or Path('parse_result')
    skip_imgs = namespace.skip_imgs or False
    skip_txt = namespace.skip_txt or False
    json_path = Path(namespace.json_path) or Path('parse_result')

    url = 'https://tululu.org/l55/'

    library = []
    with requests.Session() as session:
        books = save_links_collection(url, session, start_page, end_page, folder=json_path)

        if not end_page:
            end_page = int(list(books.keys())[-1])
        for page in range(start_page, end_page + 1):
            page = str(page)
            for book in books[page]:
                while True:
                    try:
                        resp = session.get(book)
                        resp.raise_for_status()
                        check_for_redirect(resp)

                        book = parse_book_page(resp)
                        book_path = image_src = ''
                        if not skip_txt:
                            book_path = download_txt(url=book['download_book_url'],
                                                     filename=book['title'],
                                                     session=session,
                                                     folder=dest_folder)
                            print('Скачана книга: ', book['title'])
                        if not skip_imgs:
                            image_src = download_image(url=book['image_url'], session=session, folder=dest_folder)

                        book.update({'book_path': str(book_path), 'image_src': str(image_src)})
                        library.append(book)
                        break
                    except HTTPError:
                        traceback.print_exc(limit=0)
                        break
                    except IndexError:
                        traceback.print_exc(limit=0)
                        break
                    except requests.ConnectionError:
                        if count_reconnect < 2:
                            connection_error_timeout = 30
                        traceback.print_exc(limit=0)
                        time.sleep(connection_error_timeout)
                        count_reconnect += 1
                        continue

    path = Path(json_path) / 'fantastic_books_catalog.json'
    Path.mkdir(path.parent, exist_ok=True)
    with path.open('w', encoding='utf-8') as file:
        json.dump(library, file, indent=4, ensure_ascii=False)


if __name__ == '__main__':
    main()
