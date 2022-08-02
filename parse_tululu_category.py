import json
import math
import urllib.parse
from pathlib import Path

import requests
from bs4 import BeautifulSoup


def get_links_on_the_page(response: requests.Response) -> dict:
    """
    Скачивает ссылки на книги со страницы каталога.

    :param response: объект Response.
    :return: словарь с нумерацией страниц и списком книг, максимальной страницей.
    """
    soup = BeautifulSoup(response.text, 'lxml')
    book_hrefs = [book.select_one('a').attrs['href'] for book in soup.select('.d_book')]
    current_page = soup.select_one('.npage_select').text
    max_page = soup.select('.npage')[-1].text
    book_links = [urllib.parse.urljoin('https://tululu.org/', link) for link in book_hrefs]
    book_links_collection = {current_page: book_links}
    return {'book_links': book_links_collection, 'max_page': int(max_page)}


def get_all_book_links(url, session, start_page=1, end_page=None) -> dict:
    """
    Проходит по всем страницам каталога и собирает словарь со ссылками на книги.
    Если end_page не указан, скачает весь каталог.

    :param url: ссылка на страницу каталога.
    :param session: объект сессии.
    :param start_page: страница с которой начать скачивать ссылки на книги.
    :param end_page: какую страницу с книгами скачать последней.
    :return: словарь в котором ключ: номер страницы, значение: список ссылок на книги.
    """
    if not end_page:
        end_page = math.inf
    book_links_collection = {}
    page_number = start_page
    while page_number <= end_page:
        next_url = urllib.parse.urljoin(url, str(start_page))
        resp = session.get(next_url)
        resp.raise_for_status()

        book_links = get_links_on_the_page(resp)
        book_links_collection.update(book_links.get('book_links'))
        if isinstance(end_page, float):
            end_page = book_links.get('max_page')
        page_number += 1

    return book_links_collection


def save_book_links(links: dict, filepath: Path):
    """
    Сохраняет ссылки на книги в json.

    :param links: словарь со ссылками на книги.
    :param filepath: путь до файла json.
    """
    with open(filepath, 'w', encoding='utf-8') as file:
        json.dump(links, file, indent=4, ensure_ascii=False)
