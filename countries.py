from bs4 import BeautifulSoup
import requests

url="https://worldpopulationreview.com/world-cities"
html_content = requests.get(url).text

soup = BeautifulSoup(html_content, "lxml")
table = soup.find('table', class_ = "jsx-130793")
rows = table.find_all('tr')

country_dict = {}
for row in rows[1:101]:
    data = row.find_all('td',)
    key = data[0].text.strip()
    value = data[1].text.strip()
    country_dict[key] = value
list = [(k, v) for k, v in country_dict.items()]

print(list)