import argparse
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


def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--start_id', type=int, default=1, help='с какого id начать скачивание книг.')
    parser.add_argument('-e', '--end_id', type=int, default=2, help='на каком id закончить скачивание книг.')

    return parser


def check_for_redirect(response):
    """
    Проверяет был ли редирект.

    :param response: ответ сервера.
    """
    if response.history:
        raise HTTPError('Битая ссылка.')


def download_txt(url, filename, book_id, session: Session, folder='books/'):
    """Функция для скачивания текстовых файлов.

    Args:
        url (str): Cсылка на текст, который хочется скачать.
        filename (str): Имя файла, с которым сохранять.
        folder (str): Папка, куда сохранять.
        book_id (int): id книги.
        session (Session) - сессия http-соединения.
    Returns:
        str: Путь до файла, куда сохранён текст.
    """
    os.makedirs(folder, exist_ok=True)
    resp = session.get(url)
    resp.raise_for_status()
    check_for_redirect(resp)
    filename = f'{book_id}. {sanitize_filename(filename)}'
    filepath = os.path.join(folder, filename)
    with open(f'{filepath}.txt', 'wb') as file:
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


def parse_book_page(response) -> dict:
    """
    Возвращает словарь со всеми данными о книге: название, автор и т.д.
    :param response: ответ сервера.
    :return: словарь с собранными данными.
    """
    soup = BeautifulSoup(response.text, 'lxml')
    tree = etree.HTML(response.content)

    book_name, book_author = [text.strip() for text in soup.find('h1').text.split('::')]
    if tree.xpath("//td/a[contains(@href,'/txt.php')]"):
        book_link = tree.xpath("//td/a[contains(@href,'/txt.php')]")[0].attrib['href']
    else:
        raise IndexError('Отсутствует ссылка на скачивание книги.')
    book_url = urllib.parse.urljoin(response.url, book_link)
    image = soup.find('div', class_='bookimage').a.img['src']
    image_url = urllib.parse.urljoin(response.url, image)
    comments = soup.find_all('div', class_='texts')
    book_comments = [comment.find('span', class_='black').text for comment in comments]
    raw_genres = soup.find_all('span', class_='d_book')
    genres = [genre.text for genres in raw_genres for genre in genres.find_all('a')]

    return {
        'book_name': book_name,
        'book_author': book_author,
        'book_url': book_url,
        'image_url': image_url,
        'comments': book_comments,
        'genres': genres,
    }


def main():
    connection_error_timeout = 300
    count_reconnect = 1
    parser = create_parser()
    namespace = parser.parse_args()
    start_id = namespace.start_id
    end_id = namespace.end_id

    url = 'https://tululu.org/b'
    with requests.Session() as session:
        for book_id in range(start_id, end_id + 1):
            while True:
                try:
                    resp = session.get(f'{url}{book_id}/')
                    resp.raise_for_status()
                    check_for_redirect(resp)

                    book = parse_book_page(resp)
                    download_txt(book['book_url'], book['book_name'], book_id=book_id, session=session)
                    download_image(book['image_url'], session=session)
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


if __name__ == '__main__':
    main()
