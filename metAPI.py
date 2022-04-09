import requests
import sqlite3
import os

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

    return cur, conn

def get_API(query, city_list, cur, conn):
    for city in city_list:   
        city_id = city[0]
        city_name = city[1]

        url = f"https://collectionapi.metmuseum.org/public/collection/v1/search?q=*&geoLocation={city_name}"
        data = requests.get(url)
        ids = data.json()['objectIDs']
        
        objects = []
        for id in ids:
            resp = requests.get(f'https://collectionapi.metmuseum.org/public/collection/v1/objects/{id}')
            objects.append(resp.json())
        
        for obj in objects:
            try:
                cur.execute(
                    """
                    INSERT OR IGNORE INTO Artwork (objectID, imageURL, title, cityID, artistName, artistNationality, artworkYear, medium)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (obj['objectID'], obj['primaryImage'], obj['title'], city_id, obj['artistDisplayName'], obj['artistNationality'], obj['objectDate'], obj['medium'])
                )
                conn.commit()
            except:
                print("error")
                print(obj)
        
def main():
    cur, conn = create_database('met.db')
    artists = ['Da Vinci', 'Van Gogh', 'Rembrandt van Rijn', 'Picasso', 'Monet', 'Vermeer', 'Dali', 'Rubens', 'Michelangelo', 'Rafaël']
    for artist in artists:
        get_API(artist, cur, conn)
        print('done')


if __name__ == '__main__':
    main()