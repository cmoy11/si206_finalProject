import requests
import sqlite3
import os
from os.path import exists
from bs4 import BeautifulSoup
import shutil

def create_database(name):
    path = os.path.dirname(os.path.abspath(__file__))
    conn = sqlite3.connect(path+f'/{name}')
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS Artwork
        (objectID INTEGER PRIMARY KEY, cityID INTEGER, artworkYearID INTEGER, imageURL STRING, title STRING, artistName STRING, artistNationality STRING, medium STRING)
        """
    )
    conn.commit()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS Cities
        (ID INTEGER PRIMARY KEY, city STRING)
        """
    )
    conn.commit()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS Years
        (ID INTEGER PRIMARY KEY, yearRange STRING)
        """
    )
    conn.commit()

    year_range = [('pre-1700',1), ('1700-1799',2), ('1800-1899',3), ('1900-present',4)]
    for tup in year_range:
        cur.execute(
            """
            INSERT OR IGNORE INTO Years (ID, yearRange)
            VALUES (?, ?)
            """, (tup[1], tup[0])
        )
        conn.commit()

    return cur, conn

def get_cities (start, end, cur, conn):
    url="https://worldpopulationreview.com/world-cities"
    html_content = requests.get(url).text

    soup = BeautifulSoup(html_content, "lxml")
    table = soup.find('table', class_ = "jsx-130793")
    rows = table.find_all('tr')

    city_dict = {}
    for row in rows[start + 1:end + 1]:
        data = row.find_all('td',)
        key = data[0].text.strip()
        value = data[1].text.strip()
        city_dict[int(key) - 1] = value
    list = [(k, v) for k, v in city_dict.items()]

    for i in range(25):
        cur.execute(
            """
            INSERT OR IGNORE INTO Cities (ID, city)
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

        objects = []
        for id in ids:
            if  len(objects) == 25:
                print('25 objects reached')
                break
            resp = requests.get(f'https://collectionapi.metmuseum.org/public/collection/v1/objects/{id}')
            
            try:
                if resp.json()['primaryImage']:
                    objects.append(resp.json())
                    print('valid response')
                else:
                    print('object does not have image url')
            except:
                print("inproperly formatted response")
                print(resp.json())
        
        for obj in objects:
            if int(obj['objectEndDate']) < 1700:
                year_id = 1
            elif int(obj['objectEndDate']) < 1800:
                year_id = 2
            elif int(obj['objectEndDate']) < 1900:
                year_id = 3
            else:
                year_id = 4
            
            cur.execute(
                """
                INSERT OR IGNORE INTO Artwork (objectID, cityID, artworkYearID, imageURL, title, artistName, artistNationality, medium)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (obj['objectID'], city_id, year_id, obj['primaryImage'], obj['title'], obj['artistDisplayName'], obj['artistNationality'], obj['medium'])
            )
            conn.commit()
            print('added to database')
        print('done adding to database')

def get_artwork_data(cur, conn):
    cur.execute(
        """
        SELECT Artwork.objectID, Cities.city, Years.yearRange, Artwork.imageURL
        FROM Artwork
        JOIN Cities
        ON Artwork.cityID = Cities.ID
        JOIN Years
        ON Artwork.artworkYearID = Years.ID
        """
    )
    conn.commit()
    return cur.fetchall()

def download_image(objectID, image_url):
    if not os.path.exists(f"images/{objectID}.jpg"):
        filename = f"images/{objectID}.jpg"
        r = requests.get(image_url, stream = True)
        try:
            r.raw.decode_content  = True
            with open(filename, 'wb') as f:
                shutil.copyfileobj(r.raw, f)
            print('Image sucessfully downloaded')
        except:
            print('Image failed to download')
            print(filename)
    else:
        print('file already exists')

def main():
    cur, conn = create_database('met.db')

    # first = {'start': 0, 'end': 25}
    # second = {'start': 25, 'end': 50}
    # third = {'start': 50, 'end': 75}
    # fourth = {'start': 75, 'end': 100}

    # cur.execute(
    #     """
    #     SELECT count(id) FROM Cities
    #     """
    # )
    # conn.commit()
    # data = cur.fetchall()
    # length = data[0][0]
    # print(length)
    
    # if length < 25:
    #     cities = get_cities(first['start'], first['end'], cur, conn)
    #     print(cities)
    #     get_API(cities, cur, conn)
    # elif length < 50:
    #     cities = get_cities(second['start'], second['end'], cur, conn)
    #     print(cities)
    #     get_API(cities, cur, conn)
    # elif length < 75:
    #     cities = get_cities(third['start'], third['end'], cur, conn)
    #     print(cities)
    #     get_API(cities, cur, conn)
    # else:
    #     cities = get_cities(fourth['start'], fourth['end'], cur, conn)
    #     print(cities)
    #     get_API(cities, cur, conn)
    # print('database addition complete')
    
    artwork = get_artwork_data(cur, conn)

    for art in artwork:
        download_image(art[0], art[3])
    
    print('done')

if __name__ == '__main__':
    main()