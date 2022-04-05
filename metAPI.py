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
        (objectID INTEGER PRIMARY KEY, isHighlight BOOLEAN, accessionYear INTEGER, imageURL STRING, title STRING, dynasty STRING, artistName STRING, artistNationality STRING, artistBirth INTEGER, artistDeath INTEGER, artistWikepedia STRING, artworkYear INTEGER, medium STRING, dimensions STRING, city STRING, state STRING, county STRING, region STRING, subregion STRING, wikepediaPage STRING)
        """
    )
    conn.commit()

    return cur, conn

def get_API(query, cur, conn):
    url = f"https://collectionapi.metmuseum.org/public/collection/v1/search?q={query}"
    data = requests.get(url)
    ids = data.json()['objectIDs'][:25]
    
    objects = []
    for id in ids:
        resp = requests.get(f'https://collectionapi.metmuseum.org/public/collection/v1/objects/{id}')
        objects.append(resp.json())
    
    for d in objects:
        for key in d.keys():
            if d[key] == '':
                d[key] = 'NA'

    for obj in objects:
        print(type(obj))
        cur.execute(
            """
            INSERT OR IGNORE INTO Artwork (objectID, isHighlight, accessionYear, imageURL, title, dynasty, artistName, artistNationality, artistBirth, artistDeath, artistWikepedia, artworkYear, medium, dimensions, city, state, county, region, subregion, wikepediaPage)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (obj['objectID'], obj['isHighlight'], obj['accessionYear'], obj['primaryImage'], obj['title'], obj['dynasty'], obj['artistDisplayName'], obj['artistNationality'], obj['artistBeginDate'], obj['artistEndDate'], obj['artistWikidata_URL'], obj['objectDate'], obj['medium'], obj['dimensions'], obj['city'], obj['state'], obj['county'], obj['region'], obj['subregion'], obj['objectWikidata_URL'])
        )
        conn.commit()

def main():
    cur, conn = create_database('met.db')
    get_API('sunflower', cur, conn)


if __name__ == '__main__':
    main()