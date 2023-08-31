import requests
from bs4 import BeautifulSoup
import csv

url = 'https://ixbt.com'

def get_article_link(url, base_url, link_div, link_class):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    article_link = base_url + soup.find('div', class_=link_div).find('a', class_=link_class).attrs['href']
    return article_link


def parse_article(url, base_url, article_div):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    heading = soup.find('h1').text.strip().replace(u'\xa0', u' ')
    article_content = soup.find('div', class_=article_div).find_all('p')
    article_text = ''
    for p in article_content:
        article_text += p.text.strip().replace(u'\xa0', u' ') + '\n'

    image_link = soup.find('div', class_=article_div).find('img')['src']
    if not 'http' in image_link:
        image_link = base_url + image_link

    article = {
        'heading': heading,
        'article_text': article_text,
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