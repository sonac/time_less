import requests

from bs4 import BeautifulSoup

url = 'https://www.zeit.de/2024/42/israel-7-oktober-nahostkrieg-terrorismus-hamas-palaestina'

resp = requests.get(url)
#soup = BeautifulSoup(resp.content, "html.parser")
#links = soup.find_all("a", class_="zon-teaser__link")

#hrefs = [link.get("href") for link in links]

print(resp.text)