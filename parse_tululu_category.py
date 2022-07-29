import json
import math
import urllib.parse

import requests
from bs4 import BeautifulSoup


def get_links_on_the_page(response: requests.Response) -> dict:
    """
    Скачивает ссылки на книги со страницы каталога.

    :param response: объект Response.
    :return: словарь с нумерацией страниц и списком книг, максимальной страницей.
    """
    soup = BeautifulSoup(response.text, 'lxml')
    books = soup.find_all('table', class_='d_book')
    current_page = soup.find('span', class_='npage_select').text
    max_page = soup.find_all('a', class_='npage')[-1].text
    books_collection = {}
    book_hrefs = []
    for book in books:
        book_hrefs.append(book.find('a').attrs['href'])
    book_links = [urllib.parse.urljoin('https://tululu.org/', link) for link in book_hrefs]
    books_collection.update({current_page: book_links})
    return {'books': books_collection, 'max_page': int(max_page)}


def get_all_links(url, session, start_page=1, end_page=None) -> dict:
    """
    Проходит по всем страницам каталога и собирает словарь с книгами.
    Если end_page не указан, скачает весь каталог.

    :param url: ссылка на страницу каталога.
    :param session: объект сессии.
    :param start_page: страница с которой начать скачивать ссылки на книги.
    :param end_page: какую страницу с книгами скачать последней.
    :return: словарь в котором ключ: номер страницы, значение: список ссылок на страницы книг.
    """
    if end_page is None:
        end_page = math.inf
    books_collection = {}
    while start_page <= end_page:
        next_url = urllib.parse.urljoin(url, str(start_page))
        resp = session.get(next_url)
        resp.raise_for_status()

        books = get_links_on_the_page(resp)
        books_collection.update(books.get('books'))
        if not isinstance(end_page, int):
            end_page = books.get('max_page')
        start_page += 1

    return books_collection


def save_book_links(links: dict):
    """
    Сохраняет ссылки на книги в json.

    :param links: словарь со ссылками на книги.
    """

    with open('books_collection.json', 'w') as file:
        json.dump(links, file, indent=4, ensure_ascii=False)
