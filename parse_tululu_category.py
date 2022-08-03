import math
import urllib.parse

import requests
from bs4 import BeautifulSoup


def get_links_on_the_page(response: requests.Response) -> dict:
    """
    Получает ссылки на книги со страницы каталога.

    :param response: объект Response.
    :return: словарь со списком ссылок на книги и максимальной страницей.
    """
    soup = BeautifulSoup(response.text, 'lxml')
    book_hrefs = [book.select_one('a').attrs['href'] for book in soup.select('.d_book')]
    max_page = soup.select('.npage')[-1].text
    book_links = [urllib.parse.urljoin('https://tululu.org/', link) for link in book_hrefs]
    return {'book_links': book_links, 'max_page': int(max_page)}


def get_all_book_links(url, session, start_page=1, end_page=None) -> list:
    """
    Проходит по страницам каталога и собирает ссылки на книги.
    Если end_page не указан, скачает весь каталог.

    :param url: ссылка на страницу каталога.
    :param session: объект сессии.
    :param start_page: страница с которой начать скачивать ссылки на книги.
    :param end_page: какую страницу с книгами скачать последней.
    :return: список ссылок на книги.
    """
    if not end_page:
        end_page = math.inf
    book_links_collection = []
    page_number = start_page
    while page_number <= end_page:
        next_url = urllib.parse.urljoin(url, str(page_number))
        resp = session.get(next_url)
        resp.raise_for_status()

        book_links = get_links_on_the_page(resp)
        book_links_collection.extend(book_links['book_links'])
        if isinstance(end_page, float):
            end_page = book_links.get('max_page')
        page_number += 1

    return book_links_collection
