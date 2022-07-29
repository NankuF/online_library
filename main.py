import argparse
import json
import os
import time
import traceback
import urllib.parse

import requests
from bs4 import BeautifulSoup
from lxml import etree
from pathvalidate import sanitize_filename
from requests import HTTPError
from requests.sessions import Session

from parse_tululu_category import get_all_links, save_book_links


def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--start_page', type=int, default=699, help='с какой страницы начать скачивание книг.')
    parser.add_argument('-e', '--end_page', type=int, help='какую страницу с книгами скачать последней.')

    return parser


def fetch_file_extension(url: str) -> str:
    """Получить расширение файла из url"""
    clear_path = urllib.parse.unquote(urllib.parse.urlsplit(url).path)
    return os.path.splitext(clear_path)[1]


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


def download_txt(url, filename, session: Session, folder='books/'):
    """Функция для скачивания текстовых файлов.

    Args:
        url (str): Cсылка на текст, который хочется скачать.
        filename (str): Имя файла, с которым сохранять.
        folder (str): Папка, куда сохранять.
        session (Session) - сессия http-соединения.
    Returns:
        str: Путь до файла, куда сохранён текст.
    """
    os.makedirs(folder, exist_ok=True)
    resp = session.get(url)
    resp.raise_for_status()
    check_for_redirect(resp)
    filename = f'{sanitize_filename(filename)}'
    file_extension = fetch_filename(url)
    filepath = f'{os.path.join(folder, filename)}.{file_extension}'
    with open(filepath, 'wb') as file:
        file.write(resp.content)
    return filepath


def download_image(url: str, session: Session, folder='images/'):
    """Скачать изображение"""
    os.makedirs(folder, exist_ok=True)
    resp = session.get(url)
    resp.raise_for_status()
    check_for_redirect(resp)
    filename = os.path.basename(url)
    path = os.path.join(folder, filename)

    with open(path, 'wb') as file:
        file.write(resp.content)

    return path


def parse_book_page(response) -> dict:
    """
    Возвращает словарь со всеми данными о книге: название, автор и т.д.

    :param response: ответ сервера.
    :return: словарь с собранными данными о книге.
    """
    soup = BeautifulSoup(response.text, 'lxml')
    tree = etree.HTML(response.content)

    title, author = [text.strip() for text in soup.find('h1').text.split('::')]
    if tree.xpath("//td/a[contains(@href,'/txt.php')]"):
        book_url = tree.xpath("//td/a[contains(@href,'/txt.php')]")[0].attrib['href']
    else:
        raise IndexError('Отсутствует ссылка на скачивание книги.')
    book_url = urllib.parse.urljoin(response.url, book_url)
    image = soup.find('div', class_='bookimage').a.img['src']
    image_url = urllib.parse.urljoin(response.url, image)
    comments = soup.find_all('div', class_='texts')
    comments = [comment.find('span', class_='black').text for comment in comments]
    raw_genres = soup.find_all('span', class_='d_book')
    genres = [genre.text for genres in raw_genres for genre in genres.find_all('a')]

    return {
        'title': title,
        'author': author,
        'book_url': book_url,
        'image_url': image_url,
        'comments': comments,
        'genres': genres,
    }


def check_books_collection(url, session, start_page, end_page):
    """
    Проверяет достаточно ли данных для парсинга книг.
    :param url: ссылка на каталог с книгами.
    :param session: объект сессии.
    :param start_page: страница с которой начать скачивать ссылки на книги.
    :param end_page: какую страницу с книгами скачать последней.
    :return: словарь с ссылками на книги.
    """
    last_page = end_page if end_page is not None else 'последнюю'

    if not os.path.exists('books_collection.json'):
        print(f'Скачиваю ссылки на книги c {start_page} по {last_page} страницы.')
        books_collections = get_all_links(url, start_page=start_page, end_page=end_page, session=session)
        save_book_links(books_collections)
    else:
        with open('books_collection.json', 'r') as file:
            books = json.load(file)

        if not books.get(str(end_page)) or not books.get(str(start_page)):
            print(f'Скачиваю ссылки на книги c {start_page} по {last_page} страницы.')
            books_collections = get_all_links(url, start_page=start_page, end_page=end_page, session=session)
            save_book_links(books_collections)
            with open('books_collection.json', 'r') as file:
                books = json.load(file)
    return books


def main():
    connection_error_timeout = 300
    count_reconnect = 1
    parser = create_parser()
    namespace = parser.parse_args()
    start_page, end_page = namespace.start_page, namespace.end_page

    url = 'https://tululu.org/l55/'

    library = []
    with requests.Session() as session:
        books = check_books_collection(url, session, start_page, end_page)
        if end_page is None:
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
                        book_path = download_txt(book['book_url'], book['title'], session=session)
                        image_src = download_image(book['image_url'], session=session)
                        book.update({'book_path': book_path, 'image_src': image_src})

                        library.append(book)
                        print('Скачана книга: ', book['title'])
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
    with open('fantastic_books.json', 'w', encoding='utf-8') as file:
        json.dump(library, file, indent=4, ensure_ascii=False)


if __name__ == '__main__':
    main()
