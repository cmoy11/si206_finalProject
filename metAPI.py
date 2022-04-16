import requests
import sqlite3
import os
from os.path import exists
from bs4 import BeautifulSoup
import shutil
from math import sqrt
import random
from matplotlib import image
from PIL import Image
from IPython.display import Image as CImage
from os import listdir

def create_database(name):
    path = os.path.dirname(os.path.abspath(__file__))
    conn = sqlite3.connect(path+f'/{name}')
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS Artwork
        (objectID INTEGER PRIMARY KEY, cityID INTEGER, artworkYearID INTEGER, imageURL STRING, title STRING, artistName STRING, artistNationality STRING, medium STRING, color1 STRING, color2 STRING, color3 STRING)
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

    for i in range(len(list)):
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
            try:
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
            except:
                print(f"error adding {obj['objectID']}")
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

# The following code is copied from a Python module in development. Original source: https://github.com/curiousily/Machine-Learning-from-Scratch/blob/master/4_k_means.ipynb
class Point:
  def __init__(self, coordinates):
    self.coordinates = coordinates

class Cluster:  
  def __init__(self, center, points):
    self.center = center
    self.points = points

class KMeans:  
  def __init__(self, n_clusters, min_diff = 1):
    self.n_clusters = n_clusters
    self.min_diff = min_diff
    
  def calculate_center(self, points):    
    n_dim = len(points[0].coordinates)    
    vals = [0.0 for i in range(n_dim)]    
    for p in points:
      for i in range(n_dim):
        vals[i] += p.coordinates[i]
    coords = [(v / len(points)) for v in vals]    
    return Point(coords)
  
  def assign_points(self, clusters, points):
    plists = [[] for i in range(self.n_clusters)]

    for p in points:
      smallest_distance = float('inf')

      for i in range(self.n_clusters):
        distance = euclidean(p, clusters[i].center)
        if distance < smallest_distance:
          smallest_distance = distance
          idx = i

      plists[idx].append(p)
    
    return plists
    
  def fit(self, points):
    clusters = [Cluster(center=p, points=[p]) for p in random.sample(points, self.n_clusters)]
    
    while True:

      plists = self.assign_points(clusters, points)

      diff = 0

      for i in range(self.n_clusters):
        if not plists[i]:
          continue
        old = clusters[i]
        center = self.calculate_center(plists[i])
        new = Cluster(center, plists[i])
        clusters[i] = new
        diff = max(diff, euclidean(old.center, new.center))

      if diff < self.min_diff:
        break

    return clusters

def euclidean(p, q):
  n_dim = len(p.coordinates)
  return sqrt(sum([
      (p.coordinates[i] - q.coordinates[i]) ** 2 for i in range(n_dim)
  ]))

def get_points(image_path):
  # if running on someone else's computer, change everything before /si206_finalProject/images to their own filepath
  path = os.path.dirname(os.path.abspath(__file__))
  img = Image.open(path+"/images/"+image_path)  
  # img = Image.open(image_path)
  img.thumbnail((200, 400))
  img = img.convert("RGB")
  w, h = img.size
  
  points = []
  for count, color in img.getcolors(w * h):
    for _ in range(count):
      points.append(Point(color))
  return points

def rgb_to_hex(rgb):
  return '#%s' % ''.join(('%02x' % p for p in rgb))

def get_colors(filename, n_colors=3):
  points = get_points(filename)
  clusters = KMeans(n_clusters=n_colors).fit(points)
  clusters.sort(key=lambda c: len(c.points), reverse = True)
  rgbs = [map(int, c.center.coordinates) for c in clusters]
  return list(map(rgb_to_hex, rgbs))
#End coopied code

def get_color(file):
    colors = get_colors(file, n_colors=5)
    return colors

def add_colors(cur, conn):
    artwork = get_artwork_data(cur, conn)

    for art in artwork:
        download_image(art[0], art[3])

    image_hex_list = []
    for a in artwork:
        try:
            object_id = a[0]
            city = a[1]
            yearRange = a[2]
            colors = get_colors(str(object_id) + '.jpg', n_colors=3)
            image_hex_list.append((object_id, city, yearRange, colors))
            cur.execute(
                """
                UPDATE Artwork
                SET color1  = ?, color2 = ?, color3  = ?
                WHERE objectID = ?
                """, (colors[0], colors[1], colors[2], object_id)
            )
            conn.commit()
            print(colors)
        except:
            print(f'error gathering colors from {object_id}.jpg')
            cur.execute(
                """
                DELETE FROM Artwork WHERE objectID = ?
                """, (object_id,)
            )
    return image_hex_list

def main():
    cur, conn = create_database('met.db')

    first = {'start': 0, 'end': 25}
    second = {'start': 25, 'end': 28}
    third = {'start': 28, 'end': 35}
    fourth = {'start': 35, 'end': 50}
    fifth = {'start': 50, 'end': 75}
    sixth = {'start': 75, 'end': 100}

    cur.execute(
        """
        SELECT count(id) FROM Cities
        """
    )
    conn.commit()
    data = cur.fetchall()
    length = data[0][0]
    print(length)
    
    if length < 25:
        cities = get_cities(first['start'], first['end'], cur, conn)
        print(cities)
        get_API(cities, cur, conn)
    elif length < 28:
        cities = get_cities(second['start'], second['end'], cur, conn)
        print(cities)
        get_API(cities, cur, conn)
    elif length < 35:
        cities = get_cities(third['start'], third['end'], cur, conn)
        print(cities)
        get_API(cities, cur, conn)
    elif length < 50:
        cities = get_cities(fourth['start'], fourth['end'], cur, conn)
        print(cities)
        get_API(cities, cur, conn)
    elif length < 75:
        cities = get_cities(fifth['start'], fifth['end'], cur, conn)
        print(cities)
        get_API(cities, cur, conn)
    else:
        cities = get_cities(sixth['start'], sixth['end'], cur, conn)
        print(cities)
        get_API(cities, cur, conn)
    print('database addition complete')
    
    colors = add_colors(cur, conn)
    print(colors)
    
    print('done')

if __name__ == '__main__':
    main()