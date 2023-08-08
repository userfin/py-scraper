import requests
from bs4 import BeautifulSoup
import csv

base_url = 'https://ixbt.com'

def get_article_link(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    article_link = base_url + soup.find('h2').find('a').attrs['href']
    return article_link


def parse_article(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    heading = soup.find('h1').text.strip()
    subheading = soup.find('h4').text.strip()
    article_content = soup.find('div', class_ ='b-article__content').find_all('p')
    article_text = ''
    for p in article_content:
        article_text += p.text.strip().replace(u'\xa0', u' ') + '\n'
    article_date = soup.find('p', class_='date').text.strip()
    article_author = soup.find('p', class_='author').text.strip()

    image_link = base_url + soup.find('div', class_ ='b-article__content').find('img')['src']

    article = {
        'heading': heading,
        'subheading': subheading,
        'article_text': article_text,
        'article_date': article_date,
        'article_author': article_author,
        'image_link': image_link,
        'article_link': url,
    }
    return article


def save_csv(results):
    keys = results[0].keys()

    with open('articles.csv', 'w', encoding="utf-8") as f:
        dict_writer = csv.DictWriter(f, keys)
        dict_writer.writeheader()
        dict_writer.writerows(results)
