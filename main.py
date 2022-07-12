import os

import requests

os.makedirs('books', exist_ok=True)

with requests.Session() as session:
    for i in range(1, 11):
        resp = session.get(f'https://tululu.org/txt.php?id={i}')
        resp.raise_for_status()

        with open(f'books/{i}.txt', 'wb') as file:
            file.write(resp.content)
