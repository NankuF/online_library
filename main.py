import os
import urllib.parse

import requests
from bs4 import BeautifulSoup
from lxml import etree
from pathvalidate import sanitize_filename
from requests import HTTPError


def get_url_without_scheme(url: str) -> str:
    """
    Удаляет схему из url.

    :param url:
    :return: '://tululu.org/txt.php?id=1'
    """
    url_parse = urllib.parse.urlsplit(url)
    url_without_scheme = url_parse.geturl().strip(url_parse.scheme)
    return url_without_scheme


def check_for_redirect(response):
    """
    Проверяет соответствие конечного адреса с начальным.

    :param response: ответ сервера
    :return:
    """

    if response.history:
        current_url = get_url_without_scheme(response.url)
        redirect_url = get_url_without_scheme(response.history[-1].url)
        if current_url != redirect_url:
            raise HTTPError


def download_txt(url, filename, book_id, folder='books/'):
    """Функция для скачивания текстовых файлов.

    Args:
        url (str): Cсылка на текст, который хочется скачать.
        filename (str): Имя файла, с которым сохранять.
        folder (str): Папка, куда сохранять.
    Returns:
        str: Путь до файла, куда сохранён текст.
    """
    os.makedirs(folder, exist_ok=True)
    resp = requests.get(url)
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
    resp = requests.get(url)
    resp.raise_for_status()
    filename = f'{fetch_filename(url)}{fetch_file_extension(url)}'
    path = os.path.join(folder, filename)

    with open(path, 'wb') as file:
        file.write(resp.content)


url = 'http://tululu.org/b'
with requests.Session() as session:
    for i in range(9, 11):
        resp = session.get(f'{url}{i}/')
        resp.raise_for_status()
        try:
            check_for_redirect(resp)
        except:
            print('Страница не найдена')
            continue

        soup = BeautifulSoup(resp.text, 'lxml')
        tree = etree.HTML(resp.content)

        book_name, book_author = [text.strip() for text in soup.find('h1').text.split('::')]
        try:
            # book_href = [a['href'] for a in soup.find('table', class_='d_book').find_all('a', href=True) if
            #              '/txt.php' in a['href']][0]
            book_link = tree.xpath("//td/a[contains(@href,'/txt.php')]")[0].attrib['href']
        except IndexError:
            print('Отсутствует ссылка на скачивание книги.')
            continue

        image = soup.find('div', class_='bookimage').a.img['src']
        comments = [tag.contents[4].text for tag in soup.find_all('div', class_='texts')]
        genres = [genre.strip() for genre in
                  soup.find_all('span', class_='d_book')[0].text.strip('.').split('Жанр книги: ')[1].strip().split(',')]
        image_url = urllib.parse.urljoin(resp.url, image)
        book_link_url = urllib.parse.urljoin(resp.url, book_link)
        print('Заголовок: ', book_name, '::', book_author)
        print('Link:', book_link_url)
        print('image_url:', image_url)
        print('genres:', genres)
        print('comments: ', comments)
        print('*' * 30)
        # download_txt(book_link_url, book_name, book_id=i)
        # download_image(image_url)
