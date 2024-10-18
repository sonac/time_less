import logging

import requests

from datetime import datetime, timedelta

from bs4 import BeautifulSoup

from model import Article, get_all_articles, create_new_article

base_url = "https://www.dw.com"

today = datetime.now().date()
yesterday = today - timedelta(days=1)

def parse_date(date_str):
    date_str_lower = date_str.lower()

    if 'today' in date_str_lower:
        return today
    if 'yesterday' in date_str_lower:
        return yesterday

    date_formats = [
        '%m/%d/%Y',  # e.g., '10/12/2024'
        '%Y-%m-%d'  # e.g., '2024-10-12'
    ]

    for fmt in date_formats:
        try:
            parsed_date = datetime.strptime(date_str, fmt).date()
            return parsed_date
        except ValueError:
            continue

    logging.warning(f"unable to parse date: {date_str}")
    return None

def fetch_page_content(url: str) -> str:
    """
    Fetches HTML content from a webpage.
    :param url: URL of the webpage to fetch
    :return: HTML content of the webpage
    """
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        raise Exception(f"Failed to fetch page content from {url}, Status code: {response.status_code}")


def extract_articles(html_content: str) -> list[Article]:
    soup = BeautifulSoup(html_content, 'html.parser')
    articles = []

    for block in soup.find_all('div', class_='teaser-data-wrap col-12'):
        title_tag = block.find('a')
        if title_tag:
            link = title_tag['href']
            title = title_tag.get_text()
            time_tag = block.find('time')
            date_str = time_tag.text.strip() if time_tag else 'Date not available'
            date = parse_date(date_str)
            if date in [today, yesterday]:
                articles.append(Article(title=title, link=link, date=date))

    return articles

def extract_paragraph_texts(html_content: str) -> list[str]:
    soup = BeautifulSoup(html_content, 'html.parser')
    paragraphs = [p.get_text() for p in soup.find_all('p')]
    return paragraphs

def get_today_articles():
    logging.info("starting parse of today's articles")
    full_url = f'{base_url}/en/germany/s-1432'
    html_content = fetch_page_content(full_url)
    articles = extract_articles(html_content)
    existing_articles = get_all_articles()
    relevant_articles = []
    for a in articles:
        logging.debug(f"working on the {a.title}")
        if not  a.title in [ea.title for ea in existing_articles]:
            article_html_content = fetch_page_content(f'{base_url}{a.link}')
            article_text = extract_paragraph_texts(article_html_content)
            s = "".join(article_text)
            a.text = s
            create_new_article(a)
        if a.date in [today, yesterday]:
            relevant_articles.append(a)

    return relevant_articles