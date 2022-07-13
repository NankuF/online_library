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


url = 'http://tululu.org/b'
with requests.Session() as session:
    for i in range(1, 11):
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
            continue
        if book_link:
            scheme, netloc = urllib.parse.urlsplit(resp.url).scheme, urllib.parse.urlsplit(resp.url).netloc
            book_link_url = urllib.parse.urlunsplit((scheme, netloc, book_link, '', ''))
            download_txt(book_link_url, book_name, book_id=i)
