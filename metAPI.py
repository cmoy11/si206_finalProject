import requests
import sqlite3
import os
from bs4 import BeautifulSoup
import time

def create_database(name):
    path = os.path.dirname(os.path.abspath(__file__))
    conn = sqlite3.connect(path+f'/{name}')
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS Artwork
        (objectID INTEGER PRIMARY KEY, imageURL STRING, title STRING, cityID INTEGER, artistName STRING, artistNationality STRING, artworkYear INTEGER, medium STRING)
        """
    )
    conn.commit()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS Countries
        (ID INTEGER PRIMARY KEY, country STRING)
        """
    )
    conn.commit()

    return cur, conn

def get_countries(start, end, cur, conn):
    url="https://worldpopulationreview.com/world-cities"
    html_content = requests.get(url).text

    soup = BeautifulSoup(html_content, "lxml")
    table = soup.find('table', class_ = "jsx-130793")
    rows = table.find_all('tr')

    country_dict = {}
    for row in rows[start + 1:end + 1]:
        data = row.find_all('td',)
        key = data[0].text.strip()
        value = data[1].text.strip()
        country_dict[int(key) - 1] = value
    list = [(k, v) for k, v in country_dict.items()]

    for i in range(25):
        cur.execute(
            """
            INSERT OR IGNORE INTO Countries (ID, country)
            VALUES (?, ?)
            """, (int(list[i][0]), list[i][1])
        )
        conn.commit()
    
    return list

def get_API(city_list, cur, conn):   
    for city in city_list:
        city_id = city[0]
        city_name = city[1]
            
        url = f"https://collectionapi.metmuseum.org/public/collection/v1/search?q=*&geoLocation={city_name}"
        data = requests.get(url)
        ids = data.json()['objectIDs']
        print(ids)
        if ids == None:
            print('No artwork found for this city')
            continue
        elif len(ids) < 25:
            good_ids = ids
        else:
            good_ids = ids[:25]

        objects = []
        for id in good_ids:
            resp = requests.get(f'https://collectionapi.metmuseum.org/public/collection/v1/objects/{id}')
            objects.append(resp.json())
        
        for obj in objects:
            if obj['primaryImage']:
                try:
                    cur.execute(
                        """
                        INSERT OR IGNORE INTO Artwork (objectID, imageURL, title, cityID, artistName, artistNationality, artworkYear, medium)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (obj['objectID'], obj['primaryImage'], obj['title'], city_id, obj['artistDisplayName'], obj['artistNationality'], obj['objectEndDate'], obj['medium'])
                    )
                    conn.commit()
                    print('added to database')
                except:
                    print("error")
                    print(obj)
            else:
                print('object does not have image url')
        print('done adding to database')
        
def main():
    cur, conn = create_database('met.db')

    first = {'start': 0, 'end': 25}
    second = {'start': 25, 'end': 50}
    third = {'start': 50, 'end': 75}
    fourth = {'start': 75, 'end': 100}

    cur.execute(
        """
        SELECT count(id) FROM Countries
        """
    )
    conn.commit()
    data = cur.fetchall()
    length = data[0][0]
    print(length)
    
    if length < 25:
        countries = get_countries(first['start'], first['end'], cur, conn)
        print(countries)
        get_API(countries, cur, conn)
    elif length < 50:
        countries = get_countries(second['start'], second['end'], cur, conn)
        print(countries)
        get_API(countries, cur, conn)
    elif length < 75:
        countries = get_countries(third['start'], third['end'], cur, conn)
        print(countries)
        get_API(countries, cur, conn)
    else:
        countries = get_countries(fourth['start'], fourth['end'], cur, conn)
        print(countries)
        get_API(countries, cur, conn)
    print('done')

    # print("done creating the database")
    # countries = get_countries(cur, conn)
    # get_API(countries, cur, conn)
    # print("done")


if __name__ == '__main__':
    main()