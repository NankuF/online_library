import argparse
import os
import urllib.parse

import requests
from bs4 import BeautifulSoup
from lxml import etree
from pathvalidate import sanitize_filename
from requests import HTTPError


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
        raise HTTPError


def download_txt(url, filename, book_id, folder='books/'):
    """Функция для скачивания текстовых файлов.

    Args:
        url (str): Cсылка на текст, который хочется скачать.
        filename (str): Имя файла, с которым сохранять.
        folder (str): Папка, куда сохранять.
        book_id (int): id книги.
    Returns:
        str: Путь до файла, куда сохранён текст.
    """
    os.makedirs(folder, exist_ok=True)
    resp = session.get(url)
    resp.raise_for_status()
    filename = f'{book_id}. {sanitize_filename(filename)}'
    filepath = os.path.join(folder, filename)
    with open(f'{filepath}.txt', 'wb') as file:
        file.write(resp.content)
    return filepath


def fetch_file_extension(url: str) -> str:
    """Получить расширение файла из url"""
    clear_path = urllib.parse.unquote(urllib.parse.urlsplit(url).path)
    return os.path.splitext(clear_path)[1]


def fetch_filename(url: str) -> str:
    """Получить имя файла из url, без расширения"""
    clear_path = urllib.parse.unquote(urllib.parse.urlsplit(url).path)
    return os.path.splitext(clear_path)[0].split('/')[-1]


def download_image(url: str, folder='images/'):
    """Скачать изображение"""
    os.makedirs(folder, exist_ok=True)
    resp = session.get(url)
    resp.raise_for_status()
    filename = f'{fetch_filename(url)}{fetch_file_extension(url)}'
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
        raise IndexError
    book_url = urllib.parse.urljoin(response.url, book_link)
    image = soup.find('div', class_='bookimage').a.img['src']
    image_url = urllib.parse.urljoin(response.url, image)
    comments = [tag.contents[4].text for tag in soup.find_all('div', class_='texts')]
    genres = [genre.strip() for genre in
              soup.find_all('span', class_='d_book')[0].text.strip('.').split('Жанр книги: ')[1].strip().split(',')]

    return {
        'book_name': book_name,
        'book_author': book_author,
        'book_url': book_url,
        'image_url': image_url,
        'comments': comments,
        'genres': genres,
    }


def main():
    parser = create_parser()
    namespace = parser.parse_args()
    start_id = namespace.start_id
    end_id = namespace.end_id

    url = 'https://tululu.org/b'

    for book_id in range(start_id, end_id + 1):
        resp = session.get(f'{url}{book_id}/')
        resp.raise_for_status()

        try:
            check_for_redirect(resp)
        except HTTPError:
            print('Страница не найдена.')
            continue

        try:
            parse_info = parse_book_page(resp)
        except IndexError:
            print('Отсутствует ссылка на скачивание книги.')
            continue

        download_txt(parse_info['book_url'], parse_info['book_name'], book_id=book_id)
        download_image(parse_info['image_url'])


if __name__ == '__main__':
    with requests.Session() as session:
        main()
